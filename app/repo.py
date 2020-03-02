from collections import namedtuple
from typing import Dict

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import FlushError

from app.model import engine, Doctor

# create session
Session = sessionmaker(bind=engine)
session = Session()


def session_commit() -> bool:
    ok: bool = True
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        ok = False
    except FlushError:
        ok = False
    return ok


def add_doctor(data:Dict[str, object]) -> namedtuple("doctor", "ok result"):
    doctor: Doctor = Doctor()
    for key in data:
        if hasattr(doctor, key):
            value = data[key]
            setattr(doctor, key, value)

    session.add(doctor)
    ok: bool = session_commit()
    if not ok:
        return doctor[ok, None]
    return doctor[ok, Doctor]
