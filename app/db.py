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
    country_id = Column("region_id", Integer)
    first_client_message = Column("first_client_message", DateTime)
    last_client_message = Column("last_client_message", DateTime)
    extra_comment_1 = Column("extra_comment_1", String(512))
    extra_comment_2 = Column("extra_comment_2", String(512))
    extra_comment_3 = Column("extra_comment_3", String(512))

    def __repr__(self):
        return f'id={self.id}; name="{self.name}"; phone={self.phone}, ' \
               f'assigned_name="{self.assigned_name}", comment={self.comment}'
