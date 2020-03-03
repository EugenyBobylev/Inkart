from typing import NamedTuple
import requests
import json

from app.repo import add_doctor

token = '456c1286ccf71bfcd1bda342d92a70'


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
def get_api_all_clients() -> object:
    url = "https://api.chat2desk.com/v1/clients?limit=200&offset=400"
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


# load api info json from file
def load_data_json():
    __data__ = None
    with open('c:/Users/Bobylev/My Documents/data.json', mode='r', encoding='utf-8') as f:
        __data__ = json.load(f)
    return __data__


data = None
# data = get_api_modes()
# data = get_api_transports()
# data = get_api_all_clients()
# data = get_api_channels()
# data = post_api_client(phone=79246432292 ,nick='OlgaOh')
# data = put_api_clients(client_id=96881373, client_data={"name": "EugenyBobylev"}) # EvgenyBobylev
val = put_api_clients(client_id=105582161, client_data={"name": "OlgaOh", "comment": "Ольга Владимировна Охманюк"}) # OlgaOh
val = get_api_clients(client_id=105582161)
# val = get_api_clients_phone(79247401790)
# val = post_api_message(client_id=105582161, message='Здравствуйте Ольга Владимировна!')
# chanel_id = 19286
# print(val)

result: dict = add_doctor(val['data'])
print(f"Результат добавления в БД ok={result['ok']}")
