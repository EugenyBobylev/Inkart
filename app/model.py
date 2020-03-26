from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from config import Config

conn_string = Config.SQLALCHEMY_DATABASE_URI;
Base = declarative_base()


class DataDict(object):
    @classmethod
    def from_json(cls, json_data):
        msg = cls()
        for key in json_data:
            if hasattr(msg, key):
                value = json_data[key]
                setattr(msg, key, value)
        return msg


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

    jobdoctors = relationship("JobDoctor")

    def __repr__(self):
        return f'id={self.id}; name="{self.name}"; phone={self.phone}, ' \
               f'assigned_name="{self.assigned_name}", comment={self.comment}'


# Задание на обработку
class IncartJob(Base, DataDict):
    __tablename__ = "incartjobs"

    id = Column("id", String(16), primary_key=True)
    snippet = Column("snippet", String(512))  # текст сообщения
    created = Column("created", DateTime, default=datetime.now().astimezone(timezone.utc))     # когда задание создано UTC
    doctor_id = Column("doctor_id", Integer)        # исполнитель
    closed = Column("closed", DateTime)    # метка времени UTC закрытия задания

    jobdoctors = relationship("JobDoctor")

    def __repr__(self):
        return f'id={self.id}; snippet="{self.snippet}"; created={self.created}; doctor_id={self.doctor_id}; ' \
               f'closed={self.closed}'


class JobDoctor(Base):
    __tablename__ = "jobdoctors"

    job_id = Column("job_id", String(16), ForeignKey('incartjobs.id'), primary_key=True)
    doctor_id = Column("doctor_id", Integer, ForeignKey('doctors.id'), primary_key=True, autoincrement=False)
    request_id = Column("request_id", Integer)      # id whatsapp message запроса доктору на расшифровку
    request_started = Column("request_started", DateTime)  # метка времени UTC отправки запроса доктору на расшифровку
    request_time_estimate = Column("request_time_estimate", DateTime)  # метка времени UTC ожидания получения подтверждения от доктора
    request_answer_id = Column("request_answer_id", Integer)  # id whatsapp message получения согласия на расшифровку
    answered = Column("answered", DateTime)  # метка времени UTC получения согласия на расшифровку

    job_start_id = Column("job_start_id", Integer)  # id whatsapp message отправленного доктору с заданием нарасшифровку
    job_started = Column("job_started", DateTime)  # время отправки
    job_time_estimate = Column("job_time_estimate", Integer) # Ожидаемое время окончания расшифровки
    job_finish_id = Column("job_finish_id", Integer)  # id whatsapp message с подтверждением окончания расшифровки
    job_finished = Column("job_finished", DateTime)  # время получения сообщения об окончании расшифровки

    doctor: Doctor = relationship("Doctor", back_populates='jobdoctors')
    job: IncartJob = relationship("IncartJob", back_populates='jobdoctors')

    def __repr__(self):
        return f'job_id={self.job_id}; doctor_id="{self.doctor_id}"; request_id={self.request_id}; ' \
               f'request_started={self.request_started}; request_time_estimate={self.request_time_estimate}; ' \
               f'request_answer_id={self.request_answer_id}; answered={self.answered}; job_start_id={self.job_start_id}; ' \
               f' job_started={self.job_started}; job_time_estimate={self.job_time_estimate}; ' \
               f'job_finish_id={self.job_finish_id}; job_finished={self.job_finished}'


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


class DataAccessLayer:
    def __init__(self):
        self.engine = None
        self.session = None
        self.conn_string = conn_string
        self.Session = None

    def connect(self):
        self.engine = create_engine(self.conn_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.session = self.Session()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        dal.connect()
        session = dal.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


dal = DataAccessLayer()
