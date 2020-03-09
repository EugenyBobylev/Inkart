import logging
import time
from timeloop import Timeloop
from datetime import timedelta

from app.GMailApi import get_service, get_all_unread_emails, modify_message
from app.WhatsappChanel import post_api_message
from app.model import GmailMessage

tl = Timeloop()


@tl.job(interval=timedelta(seconds=15))
def check_new_email():
    srv = get_service()
    new_messages = get_all_unread_emails(srv)
    count = len(new_messages)
    if count < 1:
        logging.info(f"You have no new email messages {time.ctime()}")
    else:
        whatsapp_msg = f"You have {count} new unread email messages {time.ctime()}"
        logging.info(whatsapp_msg)
        post_api_message(client_id=96881373, message=whatsapp_msg)
        for message in new_messages:
            logging.info(f"id={message['id']}; dody='{message['snippet']}'")
            # mark e-mail message as readed
            labels = {"removeLabelIds":  ['UNREAD'], "addLabelIds": []}
            modify_message(srv, "me", message["id"], labels)


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
        print(gmail_msg)
    # print(new_messages)
    # send_whatsapp_message('От чего же я не нахожусь?!')
    # check_new_email()
    # tl.start(block=True)
