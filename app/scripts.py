import json
import requests

from app.GMailApi import get_service, get_all_unread_emails, modify_message
import app.WhatsappChanel
from app.IncartTask import find_url_links
from app.WhatsappNotification import parse_mail_message
from app.model import dal
from app.repo import Repo

BOBYLEV = 96881373


def set_mail_unread():
    """set my gmail message as unreaded"""
    srv = get_service()
    labels = {"removeLabelIds": [], "addLabelIds": ['UNREAD']}
    modify_message(srv, "me", '1733014f3b7bea76', labels)


def get_unread_mails():
    """Get all unreaded gmail messages"""
    srv = get_service()
    unread_messages = get_all_unread_emails(srv)
    return unread_messages


def set_mail_readed():
    """check and set all gmail messages as readed"""
    srv = get_service()
    unread_messages = get_all_unread_emails(srv)
    labels = {"removeLabelIds": ['UNREAD'], "addLabelIds": []}
    for mail_msg in unread_messages:
        modify_message(srv, "me", mail_msg["id"], labels)


def count_mail_unread() -> int:
    """Get count of unreaded gmail messages"""
    _emails = get_unread_mails()
    _cnt = len(_emails)
    return _cnt


def check_gmail():
    """Check functionality my gmail api"""
    set_mail_unread()
    cnt = count_mail_unread()
    print(f'count of unread emails = {cnt}')
    if cnt > 0:
        set_mail_readed()
    cnt = count_mail_unread()
    print(f'count of unread emails = {cnt}')


def get_all_whatsapp_clients():
    clients = app.WhatsappChanel.get_api_all_clients()
    cnt = len(clients['data'])
    print_dict(clients['data'])


def get_whatsapp_bobylev():
    bobylev = app.WhatsappChanel.get_api_clients(BOBYLEV)
    print(bobylev['data'])


def send_whatsapp_message(message: str):
    app.WhatsappChanel.post_api_message(BOBYLEV, message)


def get_whatsapp_client_messages(client_id=BOBYLEV):
    """Messages sent by client"""
    messages_info = app.WhatsappChanel.get_api_messages(client_id)
    return messages_info['data']


def check_whatsapp():
    """Check functionality whatsapp api"""
    # send_whatsapp_message('сообещние отправлено через chat2desk')
    messages = get_whatsapp_client_messages()
    print_dict(messages)


def print_dict(dct):
    for item in dct:
        print(item)


def send_result():
    """sent processing result"""
    url = "http://holtershop.ru/local/backend/exchange.php"
    body = {"order_id": 605, "file": "http://holtershop.ru/upload/iblock/50d/50dd7e8f07580ac5eb6cb40389fd7a67.pdf",
            "report": "", "enc_error": ""}
    payload = json.dumps(body)
    headers = {
        'Content-Type': 'application/json',
        'charset': 'UTF-8'
    }
    response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))
    print(response.status_code)


def parse_gmail_message():
    # set_mail_unread()
    gmail_messages = get_unread_mails()
    msg = gmail_messages[0]
    print(msg)
    result = parse_mail_message(msg)
    print(result)


def db_get_incartjob():
    job_id = '1733014f3b7bea76'
    with dal.session_scope() as session:
        repo = Repo(session)
        _task = repo.get_incartjob(job_id)
        print(_task)


def test_find_url_links():
    text = 'My Profile: https://auth.geeksforgeeks.org/user/Chinmoy%20Lenka/articles ' \
           'in the portal of http://www.geeksforgeeks.org/'
    links = find_url_links(text)
    print(links)


def parse_whatsapp_msg():
    """parse doctor's whatsapp report"""
    _messages = get_whatsapp_client_messages()
    msg = _messages[-1]
    _links = find_url_links(msg['text'])
    ok = len(_links)
    print(msg["text"] + f' - это {"" if ok else " не"} ссылка')


if __name__ == '__main__':
    parse_whatsapp_msg()
    # test_find_url_links()
    # db_get_incartjob()
    # parse_gmail_message()
    # send_result()
    # check_gmail()
    # check_whatsapp()
