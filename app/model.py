from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

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


@dataclass
class ChatMessage(object):
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

    @classmethod
    def from_json(cls, json_data):
        msg = ChatMessage()
        for key in json_data:
            if hasattr(msg, key):
                value = json_data[key]
                setattr(msg, key, value)
        return msg
