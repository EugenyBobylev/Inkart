import logging
import queue
import time
from typing import List, Dict

from dateutil import parser
from timeloop import Timeloop
from datetime import timedelta, timezone, datetime

from app.GMailApi import get_service, get_all_unread_emails, modify_message
from app.Job import JobStatus
from app.WhatsappChanel import post_api_message, get_api_messages
from app.model import GmailMessage, InkartJob, Doctor, ChatMessage

tl = Timeloop()
job_queue = queue.Queue()


@tl.job(interval=timedelta(seconds=15))
def check_new_email():
    srv = get_service()
    new_messages = get_all_unread_emails(srv)
    count = len(new_messages)
    if count < 1:
        logging.info(f"run: check_new_email, no new email")
    else:
        logging.info(f"run: check_new_email, has new email(s)")
        for message in new_messages:
            job = InkartJob.from_json(message)
            logging.info(f"{job}")
            job_queue.put(job)
            # mark e-mail message as readed
            labels = {"removeLabelIds":  ['UNREAD'], "addLabelIds": []}
            modify_message(srv, "me", message["id"], labels)


@tl.job(interval=timedelta(seconds=1))
def check_job_queue():
    if not job_queue.empty():
        logging.info("run: check_job_queue")
        job: InkartJob = job_queue.get()
        run_job(job)


def send_whatsapp_message(msg):
    data = post_api_message(client_id=96881373, message=msg)
    logging.info(data)

# предложить кандидата для выполнения работы
def get_candidate() -> int:
    logging.info("run: get_candidate")
    return 96881373  # Бобылев Е.А. 96881373


def find_doctor(job: InkartJob) -> None:
    logging.info("run: find_doctor")
    # get free candidate for processing the result
    candidat_id = get_candidate()
    # send a request for processing the result
    msg = "Компания \"Инкарт\" предлагает Вам заказ на обработку результата исследования.\n" \
          "Если Вы готовы выполнить заказ, пришлите ответ со словом: Да."
    result = post_api_message(candidat_id, msg)
    status = result["status"]
    logging.info(f"={status}")
    if status != 'success':
        return
    data = result["data"]
    logging.info(f"data= {data}")
    job.request_id = data['message_id']
    job.request_started = datetime.now().astimezone(timezone.utc)
    job.request_time_estimate = job.request_started + timedelta(hours=1)
    # ждем подтверждения запроса
    confirm_request(job, candidat_id)
    if job.answered is None:
        return
    job.doctor_id = candidat_id


def confirm_request(job: InkartJob, candidat_id: int) -> None:
    logging.info("run: confirm_request")
    now = datetime.now().astimezone(timezone.utc)
    while now < job.request_time_estimate:
        logging.info("run: confirm_request while")
        val = get_api_messages(candidat_id, job.request_started)
        status = val['status']
        if status != 'success':
            continue
        data: List[Dict] = val["data"]
        last_msg = ChatMessage.from_json(data[-1])
        msg_date: datetime = parser.parse(last_msg.created)
        if job.request_started < msg_date < job.request_time_estimate:
            if last_msg.text.upper() == 'ДА':
                job.request_answer_id = last_msg.id
                job.answered = msg_date
            break
        time.sleep(30.0)


def send_job(job: InkartJob) -> None:
    logging.info("run: send_job")
    msg = "Скачайте задание <тут адрес>\n" \
          "Ждем результат через 2 ч."
    result = post_api_message(job.doctor_id, msg)
    status = result["status"]
    logging.info(f"={status}")
    if status != 'success':
        return
    data = result["data"]
    job.job_start_id = data['message_id']
    job.job_started = datetime.now().astimezone(timezone.utc)
    job.job_time_estimate = job.job_started + timedelta(hours=2, minutes=10)
    # ждем результат
    wait_processing(job)


def wait_processing(job: InkartJob) -> None:
    logging.info("run: wait_processing")
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


def send_rejection(job: InkartJob) -> None:
    logging.info("run: send_rejection")
    msg = "К сожалению мы вынуждены отменить выполнение Вами заказа."
    result = post_api_message(job.doctor_id, msg)


def send_success(job: InkartJob) -> object:
    logging.info("run: send_success")
    msg = "Подтверждаем выполнение заказа"
    result = post_api_message(job.doctor_id_id, msg)
    return object


def run_job(job: InkartJob) -> None:
    if job.doctor_id is None:
        find_doctor(job)
    if job.doctor_id is not None:
        send_job(job)
    if job.job_finish_id is None:
        send_rejection(job)  # послать отказ
    if job.job_finished is not None:
        send_success(job)    # послать подтверждение выполнения
        job.closed = datetime.now().astimezone(timezone.utc)


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    # srv = get_service()
    # new_messages = get_all_unread_emails(srv)
    # for msg in new_messages:
    #     job = InkartJob.from_json(msg)
    #     print(job)
    # print(new_messages)
    # send_whatsapp_message('От чего же я не нахожусь?!')
    # check_new_email()
    # candidat_id = 96881373
    # request_id = 360611360
    # created_str = '2020-03-10T05:08:04 UTC'
    tl.start(block=True)
