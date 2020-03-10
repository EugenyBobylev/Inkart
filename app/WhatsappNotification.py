import logging
import queue
import time
from timeloop import Timeloop
from datetime import timedelta

from app.GMailApi import get_service, get_all_unread_emails, modify_message
from app.WhatsappChanel import post_api_message
from app.model import GmailMessage, InkartJob

tl = Timeloop()
gmail_queue = queue.Queue()


@tl.job(interval=timedelta(seconds=15))
def check_new_email():
    srv = get_service()
    new_messages = get_all_unread_emails(srv)
    count = len(new_messages)
    if count < 1:
        logging.info(f"You have no new email messages {time.ctime()}")
    else:
        for message in new_messages:
            gmail_msg = GmailMessage.from_json(msg)
            logging.info(f"{gmail_msg}")
            gmail_queue.put(gmail_msg)
            # mark e-mail message as readed
            labels = {"removeLabelIds":  ['UNREAD'], "addLabelIds": []}
            modify_message(srv, "me", message["id"], labels)


@tl.job(interval=timedelta(seconds=1))
def check_gmail_queue():
    if not gmail_queue.empty():
        gmail_msg: GmailMessage = gmail_queue.get()
        whatsapp_msg = f"You have new unread email messages {gmail_msg.snippet } {time.ctime()}"
        logging.info(whatsapp_msg)
        post_api_message(client_id=96881373, message=whatsapp_msg)


def send_whatsapp_message(msg):
    data = post_api_message(client_id=96881373, message=msg)
    logging.info(data)


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.CRITICAL, datefmt="%H:%M:%S")
    srv = get_service()
    new_messages = get_all_unread_emails(srv)
    for msg in new_messages:
        gmail_msg = GmailMessage.from_json(msg)
        job = InkartJob.from_json(msg)
        print(gmail_msg)
        print('')
        print(job)
    # print(new_messages)
    # send_whatsapp_message('От чего же я не нахожусь?!')
    # check_new_email()
    # tl.start(block=True)
