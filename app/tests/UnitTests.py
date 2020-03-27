import configparser
import os
import threading
import unittest
from typing import List
from unittest.mock import patch, Mock
from datetime import datetime, timezone, timedelta

from sqlalchemy import orm

from app.WhatsappChanel import get_api_message
from app.WhatsappNotification import confirm_request, get_candidate
from app.model import dal, IncartJob, Doctor, DataAccessLayer, JobDoctor
from app.repo import Repo
from config import Config


class TestsApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        dal.conn_string = 'sqlite:///:memory:'
        dal.connect()
        dal.session = dal.Session()
        prep_db(dal.session)

    def setUp(self) -> None:
        dal.session = dal.Session()

    def tearDown(self) -> None:
        dal.session.close()

    @patch('app.WhatsappNotification.get_api_messages')
    def test_confirm_request(self, mock_get_api_message):
        self.job.request_id = 22
        self.job.request_started = datetime.now().astimezone(timezone.utc) - timedelta(minutes=20)
        self.job.request_time_estimate = self.job.request_started + timedelta(hours=1)
        t = self.job.request_started + timedelta(minutes=10)
        mock_get_api_message.return_value = {'data':
        [{'id': 360613728, 'text': 'Да', 'created': '2020-03-10T05:14:32 UTC'},
         {'id': 360837004, 'text': 'Да', 'created': t.strftime("%Y-%m-%dT%H:%M:%S %Z")}
        ], 'meta': {'total': 2, 'limit': 20, 'offset': 0},
           'status': 'success'
        }
        confirm_request(job=self.job)
        self.assertEqual(self.job.request_answer_id, 360837004)
        self.assertTrue(self.job.answered is not None)

    @patch('app.WhatsappChanel.requests.request')
    def test_get_api_message(self, mock_get):
        mock_get.return_value.text = '{"data":{"id": 22, "name": "Привет"}, "status":"success"}'
        response = get_api_message(33)
        self.assertEqual(response["status"], 'success')

    def test_dal_connection_str(self):
        dal = DataAccessLayer()
        con_string = Config.SQLALCHEMY_DATABASE_URI
        self.assertEqual(con_string, dal.conn_string)

    def test_incart_ini_exists(self):
        path = os.path.join(Config.BASEPATH, 'incart.ini')
        ok = os.path.isfile(path)
        self.assertTrue(ok)

    def test_incart_ini_read(self):
        ini = os.path.join(Config.BASEPATH, 'incart.ini')
        config = configparser.ConfigParser()
        config.read(ini)

        self.assertEqual(config["DEFAULT"].getint("check_new_email_interval"), 15)
        self.assertEqual(config["DEFAULT"].getint("check_job_queue_interval"), 5)
        self.assertEqual(config["DEFAULT"].getint("wait_confirm_request"), 30)
        self.assertEqual(config["DEFAULT"].getfloat("request_time_estimate"), 30.0)
        self.assertEqual(config["DEFAULT"].getint("wait_job_processing"), 30)
        self.assertEqual(config["DEFAULT"].getfloat("job_time_estimate"), 120.0)


class RepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        dal.conn_string = 'sqlite:///:memory:'
        dal.connect()
        dal.session = dal.Session()
        prep_db(dal.session)

    def setUp(self) -> None:
        dal.session = dal.Session()

    def tearDown(self) -> None:
        dal.session.close()

    def test_get_doctor(self):
        repo = Repo(dal.session)
        doctor = repo.get_doctor(id=1)

        self.assertIsNotNone(doctor)
        self.assertTrue(doctor.id, 1)

    def test_get_all_doctors(self):
        repo = Repo(dal.session)
        doctors = repo.get_all_doctors()
        self.assertEqual(len(doctors), 3)
        self.assertTrue(doctors[0].id, 1)
        self.assertTrue(doctors[1], 2)

    def test_get_nonexist_doctor(self):
        repo = Repo(dal.session)
        doctor = repo.get_doctor(id=-20000)
        self.assertIsNone(doctor)

    def test_get_job(self):
        repo = Repo(dal.session)
        job = repo.get_incartjob(id='1')
        self.assertIsNotNone(job)
        self.assertEqual('job_1', job.snippet)

    def test_add_job(self):
        job: IncartJob = IncartJob()
        job.id = '3'
        job.snippet = 'job_3'
        repo = Repo(dal.session)
        ok: bool = repo.add_incartjob(job)
        self.assertTrue(ok)

    def test_update_job(self):
        repo = Repo(dal.session)
        job1 = repo.get_incartjob(id='1')
        job1.doctor_id = 1
        ok: bool = repo.update_incartjob(job1)

        self.assertTrue(ok)
        job2 = repo.get_incartjob(id='1')
        self.assertEqual(job2.doctor_id, 1)

    def test_get_jobdoctor(self):
        repo = Repo(dal.session)
        jobdoctor = repo.get_jobdoctor(doctor_id=1, job_id='1')
        self.assertIsNotNone(jobdoctor)
        self.assertTrue(isinstance(jobdoctor, JobDoctor))
        self.assertTrue(jobdoctor.doctor_id == 1)
        self.assertTrue(jobdoctor.job_id == '1')
        self.assertTrue(jobdoctor.doctor.id == 1)
        self.assertTrue(jobdoctor.job.id == '1')

    def test_doctor_relations(self):
        repo = Repo(dal.session)
        doctor: Doctor = repo.get_doctor(id=1)
        self.assertIsNotNone(doctor)
        self.assertIsNotNone(doctor.jobdoctors)
        self.assertTrue(isinstance(doctor.jobdoctors, List))
        self.assertTrue(len(doctor.jobdoctors), 1)

    def test_job_relations(self):
        repo = Repo(dal.session)
        job1 = repo.get_incartjob(id='1')
        self.assertIsNotNone(job1)
        self.assertIsNotNone(job1.jobdoctors)
        self.assertTrue(isinstance(job1.jobdoctors, List))
        self.assertTrue(len(job1.jobdoctors), 2)

    def test_relations_created_doctor(self):
        doctor = Doctor(id=200, name='Пирогов')
        dal.session.commit()
        self.assertIsNotNone(doctor.jobdoctors)
        self.assertTrue(isinstance(doctor.jobdoctors, List))
        self.assertEqual(len(doctor.jobdoctors), 0)

    def test_update_jobdoctor(self):
        repo = Repo(dal.session)
        jobdoctor = repo.get_jobdoctor(doctor_id=1, job_id='1')
        jobdoctor.request_id = 23
        jobdoctor.request_started = datetime.now().astimezone(timezone.utc)
        ok: bool = repo.update_jobdoctor(jobdoctor)
        self.assertTrue(ok)

    def test_find_jobdoctor(self):
        repo = Repo(dal.session)
        job = repo.get_incartjob(id='1')
        last_jobdoctor = job.jobdoctors[-1]

        self.assertEqual(len(job.jobdoctors), 2)
        self.assertIsNotNone(last_jobdoctor)

    def test_create_jobdoctor(self):
        repo = Repo(dal.session)
        job = IncartJob()
        job.id = '200'
        job.snippet = 'test job'
        doctor = repo.get_doctor(id=1)

        jobdoctor = JobDoctor()
        jobdoctor.job = job
        jobdoctor.doctor = doctor

        ok1: bool = repo.commit()
        self.assertTrue(ok1)
        jobdoctor2 = repo.get_jobdoctor(job_id=job.id, doctor_id=doctor.id)
        self.assertIsNotNone(jobdoctor2)
        self.assertEqual(jobdoctor.doctor_id, jobdoctor2.doctor_id)
        self.assertTrue(jobdoctor.job_id, jobdoctor2.job_id)
        self.assertNotEqual(jobdoctor, jobdoctor2)

    # выбор кандидата для задания у которого есть jobdoctor
    def test_get_job_candidate(self):
        repo = Repo(dal.session)
        job = repo.get_incartjob('1')
        candidate: Doctor = repo.get_job_candidate(job)

        self.assertIsNotNone(candidate)
        self.assertTrue(isinstance(candidate, Doctor))
        self.assertEqual(candidate.id, 96881373)

    # выбор кандидата, для задания у которого еще нет jobdoctor
    def test_get_job_candidate_first(self):
        repo= Repo(dal.session)
        job = repo.get_incartjob('2')
        candidate: Doctor = repo.get_job_candidate(job)

        self.assertIsNotNone(candidate)
        self.assertTrue(isinstance(candidate, Doctor))
        self.assertEqual(candidate.id, 1)


# подготовка тестовой БД
def prep_db(session: orm.session.Session):
    doctor1 = Doctor(id=1, name='Айболит')
    doctor2 = Doctor(id=2, name='Сеченов')
    doctor3 = Doctor(id=96881373, name='EugenyBobylev')
    session.bulk_save_objects([doctor1, doctor2, doctor3])
    session.commit()

    job1 = IncartJob(id='1', snippet='job_1')
    job2 = IncartJob(id='2', snippet='job_2')
    session.bulk_save_objects([job1, job2])
    session.commit()

    job_doctor: JobDoctor = JobDoctor(job_id="1", doctor_id=1)
    job_doctor.request_id = '1'
    session.add(job_doctor)
    session.commit()

    job_doctor2 = JobDoctor(job_id="1", doctor_id=2)
    job_doctor2.request_id = '2'
    job_doctor2.request_sended = datetime.utcnow()
    session.add(job_doctor2)
    session.commit()


if __name__ == '__main__':
    unittest.main()
