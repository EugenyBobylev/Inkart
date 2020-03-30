import configparser
import logging
import os
import queue
import time
import threading
from typing import List, Dict

from dateutil import parser
from timeloop import Timeloop
from datetime import timedelta, timezone, datetime

from config import Config
from app.GMailApi import get_service, get_all_unread_emails, modify_message
from app.WhatsappChanel import post_api_message, get_api_messages
from app.model import IncartJob, ChatMessage, dal, Doctor, JobDoctor
from app.repo import Repo

tl = Timeloop()
job_queue = queue.Queue()
logger = None
dal.connect()

check_new_email_interval = 15  # интервал в сек. проверки электронной почты на появление нового задания
check_job_queue_interval = 5   # интервал в сек. проверки появления в очереди нового задания на обработку
wait_confirm_request = 30      # интервал в сек. проверки подтверждения согласия на расшифировку
request_time_estimate = 30.0   # время ожидания в мин. согласия на обработку задания, после отправки запроса
wait_job_processing = 30       # интервал в сек. проверки окончания обработки доктором задания
job_time_estimate = 120.0      # время ожидания в мин. окончания обработки задания доктором


def init():
    ini = os.path.join(Config.BASEPATH, 'incart.ini')
    if os.path.isfile(ini):
        config = configparser.ConfigParser()
        config.read(ini)
        check_new_email_interval = config["DEFAULT"].getint("check_new_email_interval")
        check_job_queue_interval = config["DEFAULT"].getint("check_job_queue_interval")
        wait_confirm_request = config["DEFAULT"].getint("wait_confirm_request")
        request_time_estimate = config["DEFAULT"].getfloat("request_time_estimate")
        wait_processing = config["DEFAULT"].getint("wait_processing")
        job_time_estimate = config["DEFAULT"].getfloat("job_time_estimate")


@tl.job(interval=timedelta(seconds=check_new_email_interval))
def check_new_email():
    srv = get_service()
    new_messages = get_all_unread_emails(srv)
    count = len(new_messages)
    if count < 1:
        log_info("run: check_new_email, no new email")
    else:
        log_info(f"run: check_new_email, has new email(s)")
        with dal.session_scope() as session:
            repo = Repo(session)
            for message in new_messages:
                job = IncartJob.from_json(message)
                ok: bool = repo.add_incartjob(job)
                if ok:
                    logger.info(f"job added to db {job}")
                    job_queue.put(job)
                    # mark e-mail message as readed
                    labels = {"removeLabelIds":  ['UNREAD'], "addLabelIds": []}
                    modify_message(srv, "me", message["id"], labels)


@tl.job(interval=timedelta(seconds=check_job_queue_interval))
def check_job_queue():
    if not job_queue.empty():
        log_info("run: check_job_queue")
        job: IncartJob = job_queue.get()
        t = threading.Thread(target=run_job, args=(job,))
        t.start()


# записать изменения состояния задачи в БД
def update_job(job: IncartJob) -> bool:
    log_info("run: update_job")
    ok: bool = False
    with dal.session_scope() as session:
        repo = Repo(session)
        ok = repo.update_incartjob(job)
    log_info(f"run: update_job, result={ok}")
    return ok


# записать изменения состояния обработки задачи в БД
def update_jobdoctor(jobdoctor: JobDoctor) -> bool:
    log_info("run: update_jobdoctor")
    ok: bool = False
    with dal.session_scope() as session:
        repo = Repo(session)
        ok: bool = repo.update_jobdoctor(jobdoctor)
    log_info(f"run: update_jobdoctor, result={ok}")
    return ok


# послать сообщение по Whatsapp
def send_whatsapp_message(msg):
    data = post_api_message(client_id=96881373, message=msg)
    log_info(data)


# присоединить задание к текущей сессии
def job_merge(job_detached: IncartJob) -> IncartJob:
    job: IncartJob = None
    with dal.session_scope() as session:
        job = session.merge(job_detached)
        cnt = len(job.jobdoctors)
    return job

def load_from_db():
    repo = Repo(dal.session)
    jobs = repo.get_jobs()

# Запустить задачу на выполнение
def run_job(job_detached: IncartJob) -> None:
    job: IncartJob = job_merge(job_detached)
    jobdoctor: JobDoctor = None
    # Найти исполнителя задания
    if job.doctor_id is None:
        jobdoctor = find_doctor(job)
    update_job(job)
    if job.doctor_id is None:
        job_queue.put(job)
        send_rejection()
        return
    # отправить задание на исполнение
    send_job(jobdoctor)
    if jobdoctor.job_finish_id is None:
        send_rejection(jobdoctor)  # послать отказ
        job.doctor_id = None
        job_queue.put(job)
        return
    # провериь выполнение задания
    if jobdoctor.job_finished is not None:
        send_success(jobdoctor)    # послать подтверждение выполнения
        job.closed = datetime.now().astimezone(timezone.utc)
    update_job(job)


# предложить кандидата для выполнения задания
def get_candidate(job: IncartJob) -> int:
    log_info("run: get_candidate")
    candidate: Doctor = None
    with dal.session_scope() as session:
        repo = Repo(session)
        # candidate = repo.get_doctor(96881373)  # Бобылев Е.А. 96881373
        candidate = repo.get_job_candidate(job)  # Бобылев Е.А. 96881373
    return candidate


# Найти исполнителя на выполнение задания
def find_doctor(job: IncartJob) -> JobDoctor:
    log_info(("run: find_doctor"))
    # get free candidate for processing the result
    candidate: Doctor = get_candidate(job)
    job.candidate_id = candidate.id

    jobdoctor = JobDoctor()  # создать объект для отслеживания состояиня обработки задания
    jobdoctor.doctor = candidate
    jobdoctor.job = job
    ok: bool = update_jobdoctor(jobdoctor)

    # send a request for processing the result
    msg = "Компания \"Инкарт\" предлагает Вам заказ на обработку результата исследования.\n" \
          "Если Вы готовы выполнить заказ, пришлите ответ со словом: Да."
    result = post_api_message(job.candidate_id, msg)
    status = result["status"]
    if status != 'success':
        return jobdoctor
    data = result["data"]
    log_info(f"data={data}")
    jobdoctor.request_id = data['message_id']
    jobdoctor.request_started = datetime.now().astimezone(timezone.utc)
    jobdoctor.request_time_estimate = jobdoctor.request_started + timedelta(minutes=request_time_estimate)
    ok = update_jobdoctor(jobdoctor)
    confirm_request(jobdoctor)
    if jobdoctor.answered is not None:
        job.doctor_id = candidate.id
    return jobdoctor


def confirm_request(jobdoctor: JobDoctor) -> None:
    log_info("run: confirm_request")
    now = datetime.now().astimezone(timezone.utc)

    while now < jobdoctor.request_time_estimate:
        log_info("run: confirm_request while")
        val = get_api_messages(jobdoctor.doctor_id, jobdoctor.request_started)
        status = val['status']
        if status != 'success':
            continue
        data: List[Dict] = val["data"]
        if len(data) > 0:
            last_msg = ChatMessage.from_json(data[-1])
            msg_date: datetime = parser.parse(last_msg.created)
            if jobdoctor.request_started < msg_date < jobdoctor.request_time_estimate:
                if last_msg.text.upper() == 'ДА':
                    jobdoctor.request_answer_id = last_msg.id
                    jobdoctor.answered = msg_date
                break
        time.sleep(wait_confirm_request)
    update_jobdoctor(jobdoctor)


# отправить задание на обработку
def send_job(jobdoctor: JobDoctor) -> None:
    log_info("run: send_job")
    msg = "Скачайте задание <тут адрес>\n" \
          "Ждем результат через 2 ч."
    result = post_api_message(jobdoctor.doctor_id, msg)
    status = result["status"]
    if status != 'success':
        return
    data = result["data"]
    jobdoctor.job_start_id = data['message_id']
    jobdoctor.job_started = datetime.now().astimezone(timezone.utc)
    jobdoctor.job_time_estimate = jobdoctor.job_started + timedelta(minutes=job_time_estimate)
    update_jobdoctor(jobdoctor)
    # ждем результат
    wait_processing(jobdoctor)


# выполнения провеоки окончания обработки задания доктором (Ожидание завершения обработки доктором)
def wait_processing(jobdoctor: JobDoctor) -> None:
    log_info("run: wait_processing")
    now = datetime.now().astimezone(timezone.utc)
    while now < jobdoctor.job_time_estimate:
        val = get_api_messages(jobdoctor.doctor_id, jobdoctor.job_started)
        status = val['status']
        if status != 'success':
            continue
        data: List[Dict] = val["data"]
        last_msg = ChatMessage.from_json(data[-1])
        msg_date: datetime = parser.parse(last_msg.created)
        if jobdoctor.job_started < msg_date < jobdoctor.job_time_estimate:
            jobdoctor.job_finish_id = last_msg.id
            jobdoctor.job_finished = parser.parse(last_msg.created)  # Это строка
            ok: bool = update_jobdoctor(jobdoctor)
            break
        time.sleep(wait_job_processing)


def send_rejection(jobdoctor: JobDoctor) -> None:
    log_info("run: send_rejection")
    msg = "К сожалению мы вынуждены отменить выполнение Вами заказа."
    post_api_message(jobdoctor.doctor_id, msg)


def send_success(jobdoctor: JobDoctor) -> None:
    log_info("run: send_success")
    msg = "Подтверждаем выполнение заказа"
    post_api_message(jobdoctor.doctor_id, msg)


def create_logger(name: str = 'test logger'):
    logger = logging.getLogger('мой логгер')
    logger.setLevel(logging.INFO)
    # create console log handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to loger
    logger.addHandler(ch)
    return logger


def log_info(msg: str):
    if logger:
        logger.info(msg)


# подготовить исходные данные
def setup_data() -> None:
    # удалить данные о задании
    repo = Repo(dal.session)
    repo.clear_jobdoctors()
    repo.clear_incartjobs()
    # mark e-mail message as unreaded
    srv = get_service()
    labels = {"removeLabelIds": [], "addLabelIds": ['UNREAD']}
    modify_message(srv, "me", '170c3a9ba451cd9e', labels)


if __name__ == "__main__":
    logger = create_logger()
    dal.connect()
    setup_data()
    init()
    # Проверка цикла работы задания
    # myjob = IncartJob()
    # myjob.id = '170c3a9ba451cd9e'
    # myjob.snippet = 'тестовое задание'
    # logger.info('помещаем задание в очередь')
    # job_queue.put(myjob)
    check_new_email()
    check_job_queue()
    #tl.start(block=True)
