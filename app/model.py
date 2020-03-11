from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

from app.Job import JobStatus
from config import Config

db_uri = Config.SQLALCHEMY_DATABASE_URI;
engine = create_engine(db_uri)
Base = declarative_base()


# данные об исполнителях из chat2desktop
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column("id", Integer, primary_key=True, autoincrement=False)
    name = Column("name", String(255))
    comment = Column("comment", String(512))
    assigned_name = Column("assigned_name", String(255))
    phone = Column("phone", Integer)
    # avatar
    region_id = Column("region_id", Integer)
    country_id = Column("country_id", Integer)
    first_client_message = Column("first_client_message", DateTime)
    last_client_message = Column("last_client_message", DateTime)
    extra_comment_1 = Column("extra_comment_1", String(512))
    extra_comment_2 = Column("extra_comment_2", String(512))
    extra_comment_3 = Column("extra_comment_3", String(512))

    def __repr__(self):
        return f'id={self.id}; name="{self.name}"; phone={self.phone}, ' \
               f'assigned_name="{self.assigned_name}", comment={self.comment}'


class DataDict(object):
    @classmethod
    def from_json(cls, json_data):
        msg = cls()
        for key in json_data:
            if hasattr(msg, key):
                value = json_data[key]
                setattr(msg, key, value)
        return msg


# chat2desk whatsapp messah=ge
@dataclass
class ChatMessage(DataDict):
    id: int
    client_id: int
    text: str
    type: str
    read: bool
    created: datetime
    dialog_id: int
    operator_id: int
    channel_id: int

    def __init__(self):
        self.id = 0
        self.client_id = 0
        self.text = ''
        self.type = 'from_client'
        self.read = False
        self.created = None
        self.dialog_id = 0
        self.operator_id = 0
        self.channel_id = 0


# gfmail message
@dataclass()
class GmailMessage(DataDict):
    id: str
    trhreadId: str
    labelIds: List[str]
    snippet: str

    def __init__(self):
        self.id = 0
        self.trhreadId = ''
        self.labelIds = []
        self.snippet = ''


# Задание на обработку
@dataclass()
class InkartJob(DataDict):
    id: str    # номер задания, id GmailMessage
    snippet: str        # текст сообщения
    created: datetime   # когда задание создано UTC
    status: JobStatus   # статус задания
    doctor_id: int      # исполнитель

    request_id: int      # id whatsapp message запроса доктору на расшифровку
    request_started: datetime  # метка времени UTC отправки запроса доктору на расшифровку
    request_time_estimate: datetime  # метка времени UTC ожидания получения подтверждения от доктора
    request_answer_id: int  # id whatsapp message получения согласия на расшифровку
    answered: datetime  # метка времени UTC получения согласия на расшифровку

    job_start_id: int  # id whatsapp message отправленного доктору с заданием нарасшифровку
    job_started: datetime  # время отправки
    job_time_estimate: datetime # Ожидаемое время окончания расшифровки

    job_finish_id: int  # id whatsapp message с подтверждением окончания расшифровки
    job_finished: datetime  # метка времени UTC с подтверждением окончания расшифровки
    closed: datetime    # метка времени UTC закрытия задания

    def __init__(self):
        self.id = ''
        self.snippet = ''
        self.created = datetime.now().astimezone(timezone.utc)
        self.status = JobStatus.CREATED
        self.doctor_id = None
        self.request_id = None
        self.request_started = None
        self.request_time_estimate = None
        self.request_answer_id =None
        self.answered = None

        self.job_start_id = None
        self.job_started = None
        self.job_time_estimate = None
        self.job_finish_id = None
        self.job_finished = None
        self.closed = None
