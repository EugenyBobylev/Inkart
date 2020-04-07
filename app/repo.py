from datetime import datetime, timezone

import sqlalchemy
from dateutil.tz import tz
from typing import Dict, List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError

from app.IncartDateTime import to_utc_datetime, to_local_datetime
from app.model import Doctor, IncartJob, JobDoctor


class Repo(object):
    def __init__(self, session):
        self.session: sqlalchemy.orm.session.Session = session

    def commit(self) -> bool:
        ok: bool = True
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            ok = False
        except FlushError:
            ok = False
        return ok

    def add_doctor(self, data: Dict[str, object]) -> bool:
        doctor: Doctor = Doctor()
        for key in data:
            if hasattr(doctor, key):
                value = data[key]
                if key == 'first_client_message' or key == 'last_client_message':
                    value = to_utc_datetime(value)  # str -> utc
                    value = to_local_datetime(value)  # utc -> local
                setattr(doctor, key, value)

        self.session.add(doctor)
        ok: bool = self.commit()
        return ok

    def get_doctor(self, id: int) -> Doctor:
        doctor: Doctor = self.session.query(Doctor).filter(Doctor.id == id).first()
        return doctor

    def del_doctor(self, id: int) -> bool:
        ok: bool = False
        doctor = self.get_doctor(id).first()
        if doctor is not None:
            self.session.delete(doctor)
            ok = self.commit()
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
        job: IncartJob = self.session.query(IncartJob).filter(IncartJob.id == id).first()
        return job

    def add_incartjob(self, job: IncartJob) -> bool:
        self.session.add(job)
        ok: bool = self.commit()
        return ok

    def update_incartjob(self, job: IncartJob) -> bool:
        self.session.add(job)
        ok: bool = self.commit()
        return ok

    def get_jobdoctor(self, doctor_id: int, job_id: str) -> JobDoctor:
        jobdoctor = self.session.query(JobDoctor)\
            .filter(JobDoctor.doctor_id == doctor_id and JobDoctor.job_id == job_id).first()
        return jobdoctor

    def update_jobdoctor(self, jobdoctor: JobDoctor) -> bool:
        self.session.add(jobdoctor)
        ok: bool = self.commit()
        return ok

    def clear_jobdoctors(self) -> bool:
        query = self.session.query(JobDoctor)
        query.delete();
        ok: bool = self.commit()
        return ok

    def clear_incartjobs(self) -> bool:
        query = self.session.query(IncartJob)
        query.delete()
        ok: bool = self.commit()
        return ok

    def get_job_candidate(self, job: IncartJob) -> Doctor:
        # найти любого врача, к которым мы не обращались с этим заданием
        doctors_id: List[int] = [x.doctor.id for x in job.jobdoctors]
        candidate: Doctor = self.session.query(Doctor).\
            filter(Doctor.id.notin_(doctors_id)).filter(Doctor.is_active).first()
        return candidate

    # get all unclosing jobs
    def get_unclosing_jobs(self) -> List[IncartJob]:
        jobs = self.session.query(IncartJob).filter(IncartJob.closed.is_(None)).all()
        for job in jobs:
            if job.doctor_id is not None:
                jobdoctor = job.jobdoctors[-1]
                # если есть отметка о выполнении доктором задания (нужно прворить результат работы)
                if jobdoctor.job_finish_id is not None and jobdoctor.job_finished is not None:
                    continue
                # если доктор дал согласие на выполнение задания
                if jobdoctor.request_answer_id is not None:
                    # если задание на выполнение не было отправлено
                    if jobdoctor.job_start_id is None:
                        job.doctor_id = None  # сброс доктора заново запускает процедуру обработки задания
                        continue
                    # задание на выполнение было отправлено
                    time_now = datetime.now().astimezone(timezone.utc)
                    # если ожидаемое время завершения обработки не наступило
                    if jobdoctor.job_started < time_now < jobdoctor.job_time_estimate:
                        continue
                job.doctor_id = None
        self.session.commit()
        return jobs
