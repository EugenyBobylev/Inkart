from __future__ import print_function
import base64
import email
import mimetypes
import pickle
import os.path
from typing import List

from apiclient import errors
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.send'
          ]


def get_message(service, user_id, msg_id):
    try:
        _message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        return _message
    except errors.HttpError as ex:
        print(f'An error occurred: \"{ex}\"')
        return None


def get_mime_message(service, user_id, msg_id):
    try:
        _message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
        print(f'{_message["snippet"]}')
        msg_str = base64.urlsafe_b64decode(_message['raw'].encode('utf-8')).decode("utf-8")
        mime_msg = email.message_from_string(msg_str)
        return mime_msg
    except errors.HttpError as exc:
        print(f'An error occurred: {exc}')


def get_attachments(service, user_id, msg_id, store_dir):
    try:
        _message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        for part in _message['payload']['parts']:
            if part['filename']:
                body = part['body']
                file_data = base64.urlsafe_b64decode(body['attachmentId'])
                path = ''.join([store_dir, part['filename']])
                f = open(path, 'wb')
                f.write(file_data)
                f.close()
    except Exception as ex:
        print(f'An error occured: {ex}')


def modify_message(service, user_id, msg_id, msg_labels):
  try:
    _message = service.users().messages().modify(userId=user_id, id=msg_id,  body=msg_labels).execute()
    return _message
  except errors.HttpError as exc:
    print(f'An error occurred: {exc}')


def get_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


def get_all_unread_emails(service) -> List[object]:
    result = list()
    results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
    messages = results.get('messages', [])
    for _message in messages:
        msg = get_message(service, user_id='me', msg_id=_message['id'])
        if msg is not None:
            result.append(msg)
    return result


def get_all_income_emails(service) -> List[object]:
    result = list()
    # Call the Gmail API to fetch INBOX
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    for _message in messages:
        msg = get_message(service, user_id='me', msg_id=_message['id'])
        result.append(msg)
    return result


def get_attach_mime(file):
    content_type, encoding = mimetypes.guess_type(file)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(file, 'rb')
        msg = MIMEText(fp.read(), subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(file, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(file, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        msg = MIMEBase(main_type, sub_type)
        with open(file, 'rb') as f:
            msg.set_payload(f.read())
        encoders.encode_base64(msg)

    filename = os.path.basename(file)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg


def create_mail(sender, to, subject, text: str) -> MIMEMultipart:
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(text, 'plain'))
    return msg


def send_gmail(service, user_id, body: MIMEMultipart):
    encoded_data = base64.urlsafe_b64encode(body.as_bytes())
    raw = encoded_data.decode()
    _message = {'raw': raw}
    try:
        _message = (service.users().messages().send(userId=user_id, body=_message).execute())
        return _message
    except errors.HttpError as ex:
        print(f'An error occurred: \"{ex}\"')


def dict_from_msg(msg_snippet: str):
    _dict = {}
    for kv in msg_snippet.split(';'):
        idx = kv.index(':')
        pair = (kv[0: idx], kv[idx+1: -1])
        _dict[pair[0]] = pair[1]
    return _dict


if __name__ == '__main__':
    # send_to = 'beabooks@mail.ru'
    # subject = "Проверка отсылки письма с вложением или без вложения"
    message = """
Это электронное письмо было послано самому себе в исключительно отладочных целях.
Оно может содержать какие-либо вложения как-то: двоичные файлы, изображения и т.д.
PS. Отправка письма возможно была сделана через gmail api
"""
    # mail_msg = create_mail('inkartpro@gmail.com', send_to, subject, message)
    # attach = 'ТехнЗадание_на_xls.docx'
    # msg_attach = get_attach_mime(attach)
    # ail_msg.attach(msg_attach)
    # msg_image = get_attach_mime('МоеФото.jpg')
    # mail_msg.attach(msg_image)
    # format = "%(asctime)s: %(message)s"
    # logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    srv = get_service()
    messages = get_all_unread_emails(srv)
    for msg in messages:
        # проверим, что реально получили message
        if 'id' in msg and 'snippet' in msg:
            msg_id = msg['id']
            snippet = msg['snippet']
            dct = dict_from_msg(snippet)
            print(dct)

    # send_gmail(srv, 'me', mail_msg)
    # get_all_income_emails(srv)

    # email_id = '16fe94817cda70f1'
    # msg = get_message(srv, 'me', email_id)
    # print(msg['snippet'])
    # get_attachments(srv, 'me', email_id, '')

    # mime_msg = get_mime_message(srv, 'me', email_id)
