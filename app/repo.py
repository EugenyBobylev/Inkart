from datetime import datetime
from dateutil.tz import tz
from typing import Dict, List

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


def to_utc_datetime(datetimestr) -> datetime:
    dt: datetime = datetime.strptime(datetimestr, '%Y-%m-%dT%H:%M:%S %Z')
    if dt.tzinfo is None:
        utc_zone = tz.gettz('UTC')
        dt = dt.replace(tzinfo=utc_zone)
    return dt


def to_local_datetime(dt: datetime) -> datetime:
    local_zone = tz.gettz()
    if dt.tzinfo is None:
        utc_zone = tz.gettz('UTC')
        dt = dt.replace(tzinfo=utc_zone)
    local_dt = dt.astimezone(local_zone)
    return local_dt


def add_doctor(data: Dict[str, object]) -> dict:
    doctor: Doctor = Doctor()
    for key in data:
        if hasattr(doctor, key):
            value = data[key]
            if key == 'first_client_message' or key == 'last_client_message':
                value = to_utc_datetime(value)      # str -> utc
                value = to_local_datetime(value)    # utc -> local
            setattr(doctor, key, value)

    session.add(doctor)
    ok: bool = session_commit()
    if not ok:
        return {"ok": ok, "doctor": None}
    return {"ok": ok, "doctor": doctor}


def get_doctor(id: int) -> Doctor:
    doctor: Doctor = session.query(Doctor).filter(Doctor.id == id).first()
    return doctor


def del_doctor(id: int) -> None:
    ok: bool = False
    doctor = get_doctor(id)
    if doctor is not None:
        session.delete(doctor)
        ok = session_commit()
    return ok


def get_dictors_id() -> List[int]:
    result = session.query(Doctor.id).all()
    lst = list()
    for item in result:
        lst.append(item.id)
    return lst
