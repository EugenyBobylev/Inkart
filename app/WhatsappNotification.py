import configparser
import logging
from pathlib import Path
import queue
from typing import List

from timeloop import Timeloop
from datetime import timedelta

from app import IncartTask
from app.IncartTask import Task
from config import Config
from app.GMailApi import get_service, get_all_unread_emails, modify_message
from app.model import IncartJob, dal
from app.repo import Repo

tl = Timeloop()
jobid_queue = queue.Queue()
logger = None
dal.connect()

check_new_email_interval = 15  # интервал в сек. проверки электронной почты на появление нового задания
check_job_queue_interval = 5   # интервал в сек. проверки появления в очереди нового задания на обработку


# Выполнить инициализацию глобальных переменных
@tl.job(interval=timedelta(seconds=10))
def init():
    ini = Path('..') / 'incart.ini'
    if ini.exists():
        config = configparser.ConfigParser()
        config.read(ini)
        global check_new_email_interval
        check_new_email_interval = config["DEFAULT"].getint("check_new_email_interval")
        global check_job_queue_interval
        check_job_queue_interval = config["DEFAULT"].getint("check_job_queue_interval")
        IncartTask.Task.init(config)


@tl.job(interval=timedelta(seconds=check_new_email_interval))
def check_new_email():
    log_info(f"run: check_new_email, new email every {check_new_email_interval} sec.")
    srv = get_service()
    new_messages = get_all_unread_emails(srv)
    count = len(new_messages)
    if count > 0:
        log_info(f"run: check_new_email, has {count} new email(s)")
        with dal.session_scope() as session:
            repo = Repo(session)
            for message in new_messages:
                job = IncartJob.from_json(message)
                ok: bool = repo.add_incartjob(job)
                if ok:
                    log_info(f"job added to db {job}")
                    jobid_queue.put(job.id)
                    # mark e-mail message as readed
                    labels = {"removeLabelIds":  ['UNREAD'], "addLabelIds": []}
                    modify_message(srv, "me", message["id"], labels)


@tl.job(interval=timedelta(seconds=check_job_queue_interval))
def check_job_queue():
    log_info(f"run: check_job_queue every {check_job_queue_interval} sec.")
    if not jobid_queue.empty():
        log_info(f"run: check_job_queue jobid_queue is not empty")
        job_id: str = jobid_queue.get()
        task = Task(job_id=job_id, queue=jobid_queue, logger=logger)
        task.start()


# загрузить очередь заданий из БД
def load_queue_from_db() -> queue.Queue:
    log_info("run: load_queue_from_db")
    repo = Repo(dal.session)
    jobs: List[IncartJob] = repo.get_unclosing_jobs()
    q: queue.Queue = queue.Queue()
    for job in jobs:
        log_info(f"load_queue_from_db: job added to queue {job}")
        q.put(job.id)
    return q


def create_logger() -> logging.Logger:
    _logger = logging.getLogger('мой логгер')
    _logger.setLevel(logging.INFO)
    # create console log handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    _logger.addHandler(ch)
    return _logger


def log_info(msg: str):
    if logger:
        logger.info(msg)


# подготовить исходные данные (пометить тестовый e-mail не прочитанным)
def set_mail_unread():
    srv = get_service()
    labels = {"removeLabelIds": [], "addLabelIds": ['UNREAD']}
    modify_message(srv, "me", '170c3a9ba451cd9e', labels)


# подготовить исходные данные (очистть БД)
def clear_data_in_db() -> None:
    # удалить данные о задании
    repo = Repo(dal.session)
    repo.clear_jobdoctors()
    repo.clear_incartjobs()


def old_main() -> None:
    # jobid_queue = load_queue_from_db()

    # Проверка цикла работы задания
    check_new_email()
    check_job_queue()

    # запустить полный цикл обработки
    # tl.start(block=True)


if __name__ == "__main__":
    # Обязательная инициализация
    logger = create_logger()
    init()
    dal.connect()
    # подготовить данные
    clear_data_in_db()
    set_mail_unread()
    # Проверка цикла работы задания
    check_new_email()
    ob_id: str = jobid_queue.get()
    print(f'{ob_id=}')
