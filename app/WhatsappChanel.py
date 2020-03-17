from datetime import date, datetime, timezone, timedelta
from typing import List, Dict
import json
import threading
import requests

from app.model import ChatMessage, dal
from app.repo import Repo

token = '456c1286ccf71bfcd1bda342d92a70'
whatsapp_data: List[Dict] = []  # список словарей содержащих данные клиентов из whatsapp channel


# chat2desk api info
def get_info() -> object:
    url = "https://api.chat2desk.com/v1/companies/api_info"
    payload = {}
    headers = {'Authorization': token}

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text) if response.ok else None
    return __data__


# chat2desk api modes
def get_api_modes() -> object:
    url = "https://api.chat2desk.com/v1/help/api_modes"
    payload = {}
    headers = {'Authorization': token}

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text) if response.ok else None
    return __data__


# chat2client api transports (Get)
def get_api_transports() -> object:
    url = "https://api.chat2desk.com/v1/help/transports"
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text) if response.ok else None
    return __data__


# chat2desk api channels (GET)
def get_api_channels() -> object:
    url = "https://api.chat2desk.com/v1/channels"
    payload = {}
    headers = {'Authorization': token}

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text) if response.ok else None
    return __data__


# chat2client api all clients (GET)
def get_api_all_clients(offset=0) -> object:
    url = f"https://api.chat2desk.com/v1/clients?offset={offset}"
    payload = {}
    headers = {'Authorization': token}

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text) if response.ok else None
    return __data__


def get_api_clients(client_id) -> object:
    url = f"https://api.chat2desk.com/v1/clients/{client_id}"
    payload = {}
    headers = {'Authorization': token}

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text) if response.ok else None
    return __data__


def get_api_clients_phone(phone) -> object:
    url = f"https://api.chat2desk.com/v1/clients?phone={phone}"
    payload = {}
    headers = {'Authorization': token}

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text) if response.ok else None
    return __data__


# chat2desk api create new client (POST)
def post_api_client(phone, nick) -> object:
    url = "https://api.chat2desk.com/v1/clients"

    # payload = '{\n\t"phone":79247401790,\n\t"transport":"viber_public"\n\t,"nickname":"EugenyBobylev"\n}'
    body = {"phone": phone, "transport":"viber_public", "nickname": nick}
    payload = json.dumps(body)
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
        'charset': 'UTF-8'
    }

    response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))
    __data__ = json.loads(response.text)
    return __data__


# chat2desk change of clint
def put_api_clients(client_id: int, client_data: dict) -> object:
    url = f"https://api.chat2desk.com/v1/clients/{client_id}"

    payload = json.dumps(client_data)
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
        'charset': 'UTF-8'
    }

    response = requests.request("PUT", url, headers=headers, data=payload.encode('utf-8'))
    __data__ = json.loads(response.text)
    return __data__


# chat2desk api send message
def post_api_message(client_id, message) -> object:
    url = "https://api.chat2desk.com/v1/messages"

    body = {"client_id": client_id, "text": message, "type": "to_client", "chanel_id": 19286, "transport": "whatsapp"}
    payload = json.dumps(body)
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
        'charset': 'UTF=8'
    }

    response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))
    __data__ = json.loads(response.text)
    return __data__


# chat2desk api get messages. Returns a list of accumulated messages (both from clients).
def get_api_messages(client_id, start_date=None) -> object:
    if start_date is None:
        start_date = date.today()
    start_date = start_date.strftime("%d-%m-%YT%H:%M:%S %Z")
    url = f"https://api.chat2desk.com/v1/messages?channel_id'=19286&type=from_client" \
          f"&client_id={client_id}&start_date={start_date}"

    payload = {}
    headers = {
        'Authorization': token
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text)
    return __data__


def get_api_message(message_id) -> object:
    url = f"https://api.chat2desk.com/v1/messages/{message_id}"
    payload = {}
    headers = {
        'Authorization': token
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text)
    return __data__


def get_api_dialogs() -> object:
    url = "https://api.chat2desk.com/v1/dialogs/?state=open"

    payload = {}
    headers = {
        'Authorization': token
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    __data__ = json.loads(response.text)
    return __data__


# load api info json from file
def load_data_json():
    __data__ = None
    with open('c:/Users/Bobylev/My Documents/data.json', mode='r', encoding='utf-8') as f:
        __data__ = json.load(f)
    return __data__


def is_continue(result) -> bool:
    meta: dict = result['meta']
    is_continue: bool = result['status'] == 'success' and \
                        meta['offset'] < meta['total']
    return is_continue


def sync_client_with_db(client_id: int) -> None:
    ok = False
    data = get_api_clients(client_id)  # запросить всю инф. по клиенту, включая каналы (нам нужен канала whatsapp)
    data = data['data']
    whatsapp_ok: bool = '19286' in str(data)
    if whatsapp_ok:
        whatsapp_data.append(data)


def sync_clients_with_db() -> None:
    dal.connect()
    repo = Repo(dal.session)
    doctors_id: List = repo.get_doctors_id()  # id докторов из БД
    threads = []    # потоки асинхронной обработки
    offset = 0
    result = get_api_all_clients(offset)  # все клиенты из chat2desk (20 записей в странице
    while is_continue(result):
        meta = result['meta']
        offset += meta['limit']
        all_clients = result['data']
        for client_data in all_clients:
            client_id = client_data['id']
            if client_id in doctors_id:
                continue
            # prepare threads
            threads.append(threading.Thread(target=sync_client_with_db, args=(client_id,)))
            # sync_client_with_db(client_id)  # выполнить синхронизацию
        # start
        for thread in threads:
            if thread.native_id is None:
                thread.start()
        result = get_api_all_clients(offset)

    # finish
    for thread in threads:
        thread.join()
    for data in whatsapp_data:
        repo.add_doctor(data)
    whatsapp_data.clear()


def get_users():
    """Get list of users"""
    response = requests.get('http://jsonplaceholder.typicode.com/users')
    if response.ok:
        return response
    return None

# data = get_api_modes()
# data = get_api_transports()
# data = get_api_channels()
# data = post_api_client(phone=79246432292 ,nick='OlgaOh')
# data = put_api_clients(client_id=96881373, client_data={"name": "EugenyBobylev"}) # EvgenyBobylev
# val = put_api_clients(client_id=105582161, client_data={"name": "OlgaOh", "comment": "Ольга Владимировна Охманюк"}) # OlgaOh
# val = get_api_clients(client_id=105582161)
# val = get_api_clients_phone(79247401790)
# val = post_api_message(client_id=105582161, message='Здравствуйте Ольга Владимировна!')
# val = get_api_dialogs()

if __name__ == "__main__":
    #val = load_data_json()
    # val = get_api_message(message_id=360611360)
    # val = get_api_all_clients(20)
    # val = post_api_message(96881373, 'Привет Евгений Александрович')
    # val = {'data': [{'id': 359976315, 'text': 'Принимаю', 'coordinates': None, 'transport': 'whatsapp', 'type': 'from_client', 'read': 1, 'created': '2020-03-08T22:24:48 UTC', 'pdf': None, 'remote_id': None, 'recipient_status': None, 'ai_tips': None, 'dialog_id': 12667967, 'operator_id': 59750, 'channel_id': 19286, 'attachments': [], 'photo': None, 'video': None, 'audio': None, 'client_id': 96881373, 'extra_data': {}}], 'meta': {'total': 1, 'limit': 20, 'offset': 0}, 'status': 'success'}
    # json_data = val['data']
    # chat_msg: ChatMessage = ChatMessage.from_json(json_data)
    # print(chat_msg)
    # chanel_id = 19286
    sync_clients_with_db()
