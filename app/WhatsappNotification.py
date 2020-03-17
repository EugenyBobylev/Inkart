import logging
import queue
import time
import threading
from typing import List, Dict

from dateutil import parser
from timeloop import Timeloop
from datetime import timedelta, timezone, datetime

from app.GMailApi import get_service, get_all_unread_emails, modify_message
from app.WhatsappChanel import post_api_message, get_api_messages
from app.model import IncartJob, ChatMessage

tl = Timeloop()
job_queue = queue.Queue()
logger = None


@tl.job(interval=timedelta(seconds=15))
def check_new_email():
    srv = get_service()
    new_messages = get_all_unread_emails(srv)
    count = len(new_messages)
    if count < 1:
        log_info("run: check_new_email, no new email")
    else:
        log_info(f"run: check_new_email, has new email(s)")
        for message in new_messages:
            job = IncartJob.from_json(message)
            logger.info(f"{job}")
            job_queue.put(job)
            # mark e-mail message as readed
            labels = {"removeLabelIds":  ['UNREAD'], "addLabelIds": []}
            modify_message(srv, "me", message["id"], labels)


@tl.job(interval=timedelta(seconds=5))
def check_job_queue():
    if not job_queue.empty():
        log_info("run: check_job_queue")
        job: IncartJob = job_queue.get()
        t = threading.Thread(target=run_job, args=(job,))
        t.start()


# Запустить задачу на выполнение
def run_job(job: IncartJob) -> None:
    if job.doctor_id is None:
        find_doctor(job)
    if job.doctor_id is not None:
        send_job(job)
    if job.job_finish_id is None:
        send_rejection(job)  # послать отказ
    if job.job_finished is not None:
        send_success(job)    # послать подтверждение выполнения
        job.closed = datetime.now().astimezone(timezone.utc)


def send_whatsapp_message(msg):
    data = post_api_message(client_id=96881373, message=msg)
    log_info(data)


# предложить кандидата для выполнения работы
def get_candidate() -> int:
    log_info("run: get_candidate")
    return 96881373  # Бобылев Е.А. 96881373


def find_doctor(job: IncartJob) -> None:
    log_info(("run: find_doctor"))
    # get free candidate for processing the result
    candidat_id = get_candidate()
    # send a request for processing the result
    msg = "Компания \"Инкарт\" предлагает Вам заказ на обработку результата исследования.\n" \
          "Если Вы готовы выполнить заказ, пришлите ответ со словом: Да."
    result = post_api_message(candidat_id, msg)
    status = result["status"]
    if status != 'success':
        return
    data = result["data"]
    log_info(f"data={data}")
    job.request_id = data['message_id']
    job.request_started = datetime.now().astimezone(timezone.utc)
    job.request_time_estimate = job.request_started + timedelta(hours=1)
    # ждем подтверждения запроса
    confirm_request(job, candidat_id)
    if job.answered is None:
        return
    job.doctor_id = candidat_id


def confirm_request(job: IncartJob, candidat_id: int) -> None:
    log_info("run: confirm_request")
    now = datetime.now().astimezone(timezone.utc)
    while now < job.request_time_estimate:
        log_info("run: confirm_request while")
        val = get_api_messages(candidat_id, job.request_started)
        status = val['status']
        if status != 'success':
            continue
        data: List[Dict] = val["data"]
        if len(data) > 0:
            last_msg = ChatMessage.from_json(data[-1])
            msg_date: datetime = parser.parse(last_msg.created)
            if job.request_started < msg_date < job.request_time_estimate:
                if last_msg.text.upper() == 'ДА':
                    job.request_answer_id = last_msg.id
                    job.answered = msg_date
                break
        time.sleep(30.0)


def send_job(job: IncartJob) -> None:
    log_info("run: send_job")
    msg = "Скачайте задание <тут адрес>\n" \
          "Ждем результат через 2 ч."
    result = post_api_message(job.doctor_id, msg)
    status = result["status"]
    if status != 'success':
        return
    data = result["data"]
    job.job_start_id = data['message_id']
    job.job_started = datetime.now().astimezone(timezone.utc)
    job.job_time_estimate = job.job_started + timedelta(hours=2, minutes=10)
    # ждем результат
    wait_processing(job)


def wait_processing(job: IncartJob) -> None:
    log_info("run: wait_processing")
    now = datetime.now().astimezone(timezone.utc)
    while now < job.job_time_estimate:
        val = get_api_messages(job.doctor_id, job.job_started)
        status = val['status']
        if status != 'success':
            continue
        data: List[Dict] = val["data"]
        last_msg = ChatMessage.from_json(data[-1])
        msg_date: datetime = parser.parse(last_msg.created)
        if job.job_started < msg_date < job.job_time_estimate:
            job.job_finish_id = last_msg.id
            job.job_finished = last_msg.created
            break
        time.sleep(30.0)


def send_rejection(job: IncartJob) -> None:
    log_info("run: send_rejection")
    msg = "К сожалению мы вынуждены отменить выполнение Вами заказа."
    result = post_api_message(job.doctor_id, msg)


def send_success(job: IncartJob) -> object:
    log_info("run: send_success")
    msg = "Подтверждаем выполнение заказа"
    result = post_api_message(job.doctor_id, msg)
    return object


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


if __name__ == "__main__":
    logger = create_logger()
    # Проверка цикла работы задания
    # myjob = IncartJob()
    # myjob.id = '170c3a9ba451cd9e'
    # myjob.snippet = 'тестовое задание'
    # logger.info('помещаем задание в очередь')
    # job_queue.put(myjob)
    # check_job_queue()
    # tl.start(block=True)
