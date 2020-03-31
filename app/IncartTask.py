import configparser
import os
import threading
import time
from datetime import timedelta, datetime, timezone
from logging import Logger
from queue import Queue
from typing import List, Dict

from dateutil import parser

from app.WhatsappChanel import post_api_message, get_api_messages
from app.model import DataAccessLayer, IncartJob, JobDoctor, Doctor, ChatMessage
from app.repo import Repo
from config import Config


class Task(threading.Thread):
    wait_confirm_request = 30  # интервал в сек. проверки подтверждения согласия на расшифировку
    request_time_estimate = 30.0  # время ожидания в мин. согласия на обработку задания, после отправки запроса
    wait_job_processing = 30  # интервал в сек. проверки окончания обработки доктором задания
    job_time_estimate = 120.0  # время ожидания в мин. окончания обработки задания доктором

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
        # Найти исполнителя задания
        if job.doctor_id is None:
            jobdoctor = self.find_doctor(job)
        self.update_job(job)
        if job.doctor_id is None:
            self.queue.put(job.id)
            self.send_rejection(jobdoctor)
            return
        # отправить задание на исполнение
        self.send_job(jobdoctor)
        if jobdoctor.job_finish_id is None:
            self.send_rejection(jobdoctor)  # послать отказ
            job.doctor_id = None
            self.queue.put(job.id)
            return
        # провериь выполнение задания
        if jobdoctor.job_finished is not None:
            self.send_success(jobdoctor)  # послать подтверждение выполнения
            job.closed = datetime.now().astimezone(timezone.utc)
        self.update_job(job)

    # Найти исполнителя на выполнение задания
    def find_doctor(self, job: IncartJob) -> JobDoctor:
        self.log_info("run: find_doctor")
        # get free candidate for processing the result
        candidate: Doctor = self.get_candidate(job)

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
        return jobdoctor

    # предложить кандидата для выполнения задания
    def get_candidate(self, job: IncartJob) -> int:
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
                    break
            time.sleep(Task.wait_confirm_request)
        self.update_jobdoctor(jobdoctor)

    # отправить задание на обработку
    def send_job(self, jobdoctor: JobDoctor) -> None:
        self.log_info("run: send_job")
        msg = "Скачайте задание <тут адрес>\n" \
              "Ждем результат через 2 ч."
        result = post_api_message(jobdoctor.doctor_id, msg)
        status = result["status"]
        if status != 'success':
            return
        data = result["data"]
        jobdoctor.job_start_id = data['message_id']
        jobdoctor.job_started = datetime.now().astimezone(timezone.utc)
        jobdoctor.job_time_estimate = jobdoctor.job_started + timedelta(minutes=Task.job_time_estimate)
        self.update_jobdoctor(jobdoctor)
        # ждем результат
        self.wait_processing(jobdoctor)

    # выполнения провеоки окончания обработки задания доктором (Ожидание завершения обработки доктором)
    def wait_processing(self, jobdoctor: JobDoctor) -> None:
        self.log_info("run: wait_processing")
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
    def init():
        ini = os.path.join(Config.BASEPATH, 'incart.ini')
        if os.path.isfile(ini):
            config = configparser.ConfigParser()
            config.read(ini)
            Task.wait_confirm_request = config["DEFAULT"].getint("wait_confirm_request")
            Task.request_time_estimate = config["DEFAULT"].getfloat("request_time_estimate")
            Task.wait_processing = config["DEFAULT"].getint("wait_processing")
            Task.job_time_estimate = config["DEFAULT"].getfloat("job_time_estimate")
