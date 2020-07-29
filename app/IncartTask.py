import configparser
import re
import threading
import time
from datetime import timedelta, datetime, timezone
from logging import Logger
from queue import Queue
from typing import List, Dict

from dateutil import parser

from app.IncartDateTime import get_wait_time, get_delay_time
from app.WhatsappChanel import post_api_message, get_api_messages
from app.model import DataAccessLayer, IncartJob, JobDoctor, Doctor, ChatMessage
from app.repo import Repo


# найти все url в переданной строке
def find_url_links(txt) -> List:
    """Find all url links in input string"""
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|" \
            r"(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, txt)
    return [x[0] for x in url]


class Task(threading.Thread):
    wait_confirm_request = 30  # интервал в сек. проверки подтверждения согласия на расшифировку
    request_time_estimate = 30.0  # время ожидания в мин. согласия на обработку задания, после отправки запроса
    wait_job_processing = 30  # интервал в сек. проверки окончания обработки доктором задания
    job_time_estimate = 120.0  # время ожидания в мин. окончания обработки задания доктором
    job_delay = 180.0  # время задержки выполнения задачи в мин. (задача отложена из за невозможности найти исполнителя)

    def __init__(self, job_id: str, queue: Queue, logger: Logger):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.dal = DataAccessLayer()
        self.dal.connect()
        self.job_id: str = job_id
        self.queue = queue
        self.logger: Logger = logger

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        """
        Run the thread
        """
        self.run_job()

    # Запустить задачу на выполнение
    def run_job(self) -> None:
        repo = Repo(self.dal.session)
        job: IncartJob = repo.get_incartjob(self.job_id)
        jobdoctor: JobDoctor = None

        # искать исполнителя задания
        if job.doctor_id is None:
            jobdoctor = self.find_doctor(job)
        # исполнитель не найден(не нашли кандидата)
        if jobdoctor is None:
            self.set_restart_datetime(job)
            return
        # исполнитель не найден (кандидат отказалася)
        if job.doctor_id is None:
            self.stop_job(jobdoctor)
            return
        # отправить задание на исполнение
        self.send_job(jobdoctor)
        if jobdoctor.job_finish_id is None:
            self.stop_job(jobdoctor)
            return
        # задание не было выполнено в срок
        if jobdoctor.job_finished is None:
            self.stop_job(jobdoctor)
            return
        # доктор подтвердил выполнение задания
        job.closed = datetime.now().astimezone(timezone.utc)
        self.update_job(job)
        self.send_success(jobdoctor)  # послать подтверждение выполнения

    # перекратить обработку задания, отослать кандитату или исполнителю отказ
    def stop_job(self, jobdoctor: JobDoctor):
        job: JobDoctor = jobdoctor.job
        job.doctor_id = None
        self.update_job(job)
        self.queue.put(job.id)
        self.send_rejection(jobdoctor)  # послать отказ

    # расчитать и записать в задание время следующего рестарта
    def set_restart_datetime(self, job):
        now_utc = datetime.now().astimezone(timezone.utc)
        job.restart = get_delay_time(now_utc, wait=Task.job_delay)
        self.update_job(job)

    # Найти исполнителя на выполнение задания
    def find_doctor(self, job: IncartJob) -> JobDoctor:
        self.log_info("run: find_doctor")
        # get free candidate for processing the result
        candidate: Doctor = self.get_candidate(job)
        if candidate is None:
            return None  # прекращаем дальнейщий поиск если нет кандидата

        jobdoctor = JobDoctor()  # создать объект для отслеживания состояиня обработки задания
        jobdoctor.doctor = candidate
        jobdoctor.job = job
        ok: bool = self.update_jobdoctor(jobdoctor)

        # send a request for processing the result
        msg = "Компания \"Инкарт\" предлагает Вам заказ на обработку результата исследования.\n" \
              "Если Вы готовы выполнить заказ, пришлите ответ со словом: Да."
        result = post_api_message(candidate.id, msg)
        status = result["status"]
        if status != 'success':
            return jobdoctor
        data = result["data"]
        self.log_info(f"data={data}")
        jobdoctor.request_id = data['message_id']
        jobdoctor.request_started = datetime.now().astimezone(timezone.utc)
        jobdoctor.request_time_estimate = jobdoctor.request_started + timedelta(minutes=Task.request_time_estimate)
        ok = self.update_jobdoctor(jobdoctor)
        self.confirm_request(jobdoctor)
        if jobdoctor.answered is not None:
            job.doctor_id = candidate.id
            self.update_job(job)
        return jobdoctor

    # предложить кандидата для выполнения задания
    def get_candidate(self, job: IncartJob) -> Doctor:
        self.log_info("run: get_candidate")
        repo = Repo(self.dal.session)
        candidate: Doctor = repo.get_job_candidate(job)  # Бобылев Е.А. 96881373
        return candidate

    # ожидать подтвеждение от кандидата согласия на выполнения задания
    def confirm_request(self, jobdoctor: JobDoctor) -> None:
        self.log_info("run: confirm_request")
        now = datetime.now().astimezone(timezone.utc)

        while now < jobdoctor.request_time_estimate:
            self.log_info("run: confirm_request while")
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
                    self.log_info(F"run conffirm_request msg.text={last_msg.text}")
                    break
            time.sleep(Task.wait_confirm_request)
            now = datetime.now().astimezone(timezone.utc)
        self.update_jobdoctor(jobdoctor)

    # отправить задание на обработку
    def send_job(self, jobdoctor: JobDoctor) -> None:
        self.log_info("run: send_job")
        start = datetime.now()
        finish = get_wait_time(start, wait=Task.job_time_estimate)
        link = jobdoctor.job.file_encrypt
        msg = f"Скачайте задание {link}\n" \
              f"Ждем результат  {finish}."
        result = post_api_message(jobdoctor.doctor_id, msg)
        status = result["status"]
        if status != 'success':
            return
        data = result["data"]
        jobdoctor.job_start_id = data['message_id']
        jobdoctor.job_started = start.astimezone(timezone.utc)
        jobdoctor.job_time_estimate = finish.astimezone(timezone.utc)
        self.update_jobdoctor(jobdoctor)
        # ждем результат
        self.wait_processing(jobdoctor)

    # выполнения провеоки окончания обработки задания доктором (Ожидание завершения обработки доктором)
    def wait_processing(self, jobdoctor: JobDoctor) -> None:
        self.log_info("run: wait_processing")
        now_utc = datetime.now().astimezone(timezone.utc)
        while now_utc < jobdoctor.job_time_estimate:
            val = get_api_messages(jobdoctor.doctor_id, jobdoctor.job_started)
            status = val['status']
            if status != 'success':
                continue
            data: List[Dict] = val["data"]
            last_msg = ChatMessage.from_json(data[-1])
            msg_date: datetime = parser.parse(last_msg.created)
            if jobdoctor.job_started < msg_date < jobdoctor.job_time_estimate:
                urls = find_url_links(last_msg['text'])
                if len(urls) > 0:
                    jobdoctor.job.file_decrypt = urls[0]
                else:
                    jobdoctor.job.enc_error = last_msg['text']
                jobdoctor.job_finish_id = last_msg.id
                jobdoctor.job_finished = parser.parse(last_msg.created)  # Это строка
                self.update_jobdoctor(jobdoctor)
                break
            time.sleep(Task.wait_job_processing)

    # записать изменения состояния задачи в БД
    def update_job(self, job: IncartJob) -> bool:
        self.log_info("run: update_job")
        repo = Repo(self.dal.session)
        ok: bool = repo.update_incartjob(job)
        self.log_info(f"run: update_job, result={ok}")
        return ok

    # записать изменения состояния обработки задачи в БД
    def update_jobdoctor(self, jobdoctor: JobDoctor) -> bool:
        self.log_info("run: update_jobdoctor")
        repo = Repo(self.dal.session)
        ok: bool = repo.update_jobdoctor(jobdoctor)
        self.log_info(f"run: update_jobdoctor, result={ok}")
        return ok

    # записать в лог
    def log_info(self, msg: str):
        if self.logger:
            self.logger.info(msg)

    # послать отказ по wahtsapp
    def send_rejection(self, jobdoctor: JobDoctor) -> None:
        self.log_info("run: send_rejection")
        msg = "К сожалению мы вынуждены отменить выполнение Вами заказа."
        post_api_message(jobdoctor.doctor_id, msg)

    # послать подтверждение по whatsapp
    def send_success(self, jobdoctor: JobDoctor) -> None:
        self.log_info("run: send_success")
        msg = "Подтверждаем выполнение заказа"
        post_api_message(jobdoctor.doctor_id, msg)

    # Выполнить инициализацию глобальных переменных
    @staticmethod
    def init(config: configparser.ConfigParser):
        Task.wait_confirm_request = config["DEFAULT"].getint("wait_confirm_request")
        Task.request_time_estimate = config["DEFAULT"].getfloat("request_time_estimate")
        Task.wait_job_processing = config["DEFAULT"].getint("wait_job_processing")
        Task.job_time_estimate = config["DEFAULT"].getfloat("job_time_estimate")
        Task.job_delay = config["DEFAULT"].getfloat("job_delay")
