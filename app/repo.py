from datetime import datetime

import sqlalchemy
from dateutil.tz import tz
from typing import Dict, List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError

from app.model import DataAccessLayer, Doctor, IncartJob


class Repo(object):
    def __init__(self, session):
        self.session: sqlalchemy.orm.session.Session = session

    def session_commit(self) -> bool:
        ok: bool = True
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            ok = False
        except FlushError:
            ok = False
        return ok

    def add_doctor(self, data: Dict[str, object]) -> dict:
        doctor: Doctor = Doctor()
        for key in data:
            if hasattr(doctor, key):
                value = data[key]
                if key == 'first_client_message' or key == 'last_client_message':
                    value = to_utc_datetime(value)  # str -> utc
                    value = to_local_datetime(value)  # utc -> local
                setattr(doctor, key, value)

        self.session.add(doctor)
        ok: bool = self.session_commit()
        if not ok:
            return {"ok": ok, "doctor": None}
        return {"ok": ok, "doctor": doctor}

    def get_doctor(self, id: int) -> Doctor:
        doctor: Doctor = self.session.query(Doctor).filter(Doctor.id == id).first()
        return doctor

    def del_doctor(self, id: int) -> bool:
        ok: bool = False
        doctor = self.get_doctor(id)
        if doctor is not None:
            self.session.delete(doctor)
            ok = self.session_commit()
        return ok

    def get_doctors_id(self) -> List[int]:
        result = self.session.query(Doctor.id).all()
        lst = list()
        for item in result:
            lst.append(item.id)
        return lst

    def get_all_doctors(self) -> List[Doctor]:
        result = self.session.query(Doctor).all()
        return result

    def get_incartjob(self, id: str) -> IncartJob:
        job: IncartJob = self.session.query(IncartJob).filter(IncartJob.id == id)
        return job

    def add_incartjob(self, job: IncartJob) -> dict:
        self.session.add(job)
        ok: bool = self.session_commit()
        if not ok:
            return {"ok": ok, "job": None}
        return {"ok": ok, "job": job}


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
