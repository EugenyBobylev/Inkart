from app.GMailApi import get_service, get_all_unread_emails, modify_message
import app.WhatsappChanel


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
    messages_info = app.WhatsappChanel.get_api_messages(BOBYLEV)
    return messages_info['data']


def check_whatsapp():
    """Check functionality whatsapp api"""
    # send_whatsapp_message('сообещние отправлено через chat2desk')
    messages = get_whatsapp_client_messages()
    print_dict(messages)


def print_dict(dct):
    for item in dct:
        print(item)


if __name__ == '__main__':
    # check_gmail()
    check_whatsapp()