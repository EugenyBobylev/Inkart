import configparser
import os
import unittest
from typing import List
from unittest.mock import patch, Mock
import datetime

from sqlalchemy import orm

from app import IncartTask
from app.IncartDateTime import get_today, get_today_night_start, get_tomorrow_night_finish, add_minutes, round_datetime, \
    get_local_timezone, get_delay_time, get_wait_time
from app.WhatsappChanel import get_api_message
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

        self.assertTrue(config["DEFAULT"].getint("check_new_email_interval") > 0)
        self.assertTrue(config["DEFAULT"].getint("check_job_queue_interval") > 0)
        self.assertTrue(config["DEFAULT"].getint("wait_confirm_request") > 0)
        self.assertTrue(config["DEFAULT"].getfloat("request_time_estimate") > 0.0)
        self.assertTrue(config["DEFAULT"].getint("wait_job_processing") > 0)
        self.assertTrue(config["DEFAULT"].getfloat("job_time_estimate") > 0.0)
        self.assertTrue(config["DEFAULT"].getfloat("job_delay") > 0.0)
        self.assertTrue(isinstance(config["DEFAULT"]["night_start"], str))
        self.assertEqual(config["DEFAULT"]["night_start"], '21:00:00')
        self.assertEqual(config["DEFAULT"]["night_finish"], '09:00:00')

    def test_icart_task_init(self):
        IncartTask.Task.wait_confirm_request = 0
        IncartTask.Task.request_time_estimate = 0.0
        IncartTask.Task.wait_job_processing = 0
        IncartTask.Task.job_time_estimate = 0.0
        IncartTask.Task.job_delay = 0.0

        ini = os.path.join(Config.BASEPATH, 'incart.ini')
        config = configparser.ConfigParser()
        config.read(ini)
        IncartTask.Task.init(config)

        self.assertTrue(IncartTask.Task.wait_confirm_request > 0)
        self.assertTrue(IncartTask.Task.request_time_estimate > 0.0)
        self.assertTrue(IncartTask.Task.wait_job_processing > 0)
        self.assertTrue(IncartTask.Task.job_time_estimate > 0.0)
        self.assertTrue(IncartTask.Task.job_delay > 0.0)

    # тестируем учет ночных часов
    def test_night_hours(self):
        today = datetime.date.today()
        night_start = datetime.time.fromisoformat('21:00:00')
        today_night_start = datetime.datetime.combine(today, night_start)
        tomorrow = today + datetime.timedelta(days=1)
        night_end = datetime.time.fromisoformat('09:00:00')
        tomorrow_night_end = datetime.datetime.combine(tomorrow, night_end)
        night = tomorrow_night_end - today_night_start
        night_hours = night.seconds / 3600

        self.assertTrue(isinstance(night, datetime.timedelta))
        self.assertEqual(night_hours, 12)

    # тест для првоерки модуля IncartDateTime
    def test_night_incartdatetime(self):
        today_night_start: datetime.datetime = get_today_night_start()
        tomorrow_night_finish: datetime.datetime = get_tomorrow_night_finish()
        night: datetime.timedelta = tomorrow_night_finish - today_night_start
        night_hours = night.seconds / 3600

        self.assertTrue(isinstance(night_hours, float))
        self.assertEqual(night_hours, 12)

    def test_add_minutes(self):
        dt = datetime.datetime(2020, 6, 10, 0, 0)
        dt_plus_30 = add_minutes(dt,30)
        dt_minus_30 = add_minutes(dt, -30)

        self.assertEqual(dt_plus_30, datetime.datetime(2020, 6, 10, 0, 30))
        self.assertEqual(dt_minus_30, datetime.datetime(2020, 6, 9, 23, 30))

    def test_round_datetime_90(self):
        today: datetime.date = get_today()
        time = datetime.time.fromisoformat("09:48:12.345")
        dt_before = datetime.datetime.combine(today,time)
        dt_after = round_datetime(dt_before, 90)

        self.assertEqual(dt_after.hour, 11)
        self.assertEqual(dt_after.minute, 0)
        self.assertEqual(dt_after.second,0)
        self.assertEqual(dt_after.microsecond,0)

    def test_round_datetime_30(self):
        dt_before = datetime.datetime.fromisoformat('2020-04-09 09:12:34.123456')
        dt_before = add_minutes(dt_before, 180.0)
        dt_after = round_datetime(dt_before, 30)
        self.assertEqual(dt_after, datetime.datetime.fromisoformat('2020-04-09 12:30:00'))

    def test_round_datetime_15(self):
        today: datetime.date = get_today()
        time1 = datetime.time.fromisoformat("09:18:12.345987")
        dt1 = datetime.datetime.combine(today, time1)
        dt_after1 = round_datetime(dt1, 15)  # 09:30:00

        time2 = datetime.time.fromisoformat("09:00:12")
        dt2 = datetime.datetime.combine(today, time2)
        dt_after2 = round_datetime(dt2, 15)  # 09:00:00

        time3 = datetime.time.fromisoformat("09:53:12")
        dt3 = datetime.datetime.combine(today, time3)
        dt_after3 = round_datetime(dt3, 15)  # 10:00:00

        self.assertEqual(dt_after1.hour, 9)
        self.assertEqual(dt_after1.minute, 30)
        self.assertEqual(dt_after2.hour, 9)
        self.assertEqual(dt_after2.minute, 0)
        self.assertEqual(dt_after3.hour, 10)
        self.assertEqual(dt_after3.minute, 0)

    def test_local_timezone(self):
        local_tz = get_local_timezone()
        now = datetime.datetime.now()
        timezone_name = local_tz.tzname(now)
        self.assertEqual(timezone_name, 'UTC+10:00')

    @patch('app.IncartDateTime.get_night_start')
    @patch('app.IncartDateTime.get_night_finish')
    def test_get_restart_job_without_night(self, mock_get_night_finish, mock_get_night_start):
        # настройка значений возвращемых mock - объектами
        mock_get_night_start.return_value = datetime.time.fromisoformat('21:00:00')
        mock_get_night_finish.return_value = datetime.time.fromisoformat('09:00:00')

        delay_start1 = datetime.datetime.fromisoformat('2020-04-09 09:12:34.123456')
        delay_finish1 = get_delay_time(delay_start1, 180.0, 30)
        self.assertTrue(isinstance(delay_finish1, datetime.datetime))
        self.assertEqual(datetime.datetime.fromisoformat('2020-04-09 12:30:00'), delay_finish1)

    @patch('app.IncartDateTime.get_night_start')
    @patch('app.IncartDateTime.get_night_finish')
    def test_get_restart_job_with_night_1(self, mock_get_night_finish, mock_get_night_start):
        # настройка значений возвращемых mock - объектами
        mock_get_night_start.return_value = datetime.time.fromisoformat('21:00:00')
        mock_get_night_finish.return_value = datetime.time.fromisoformat('09:00:00')

        # старт задержки до начала ночи, окончание ночью
        delay_start1 = datetime.datetime.fromisoformat('2020-04-09 19:20:34.123456')
        delay_finish1 = get_delay_time(delay_start1, 180.0, 30)
        # старт задержки ночью, окончание ночью
        delay_start2 = datetime.datetime.fromisoformat('2020-04-09 23:20:34.123456')
        delay_finish2 = get_delay_time(delay_start2, 180.0, 30)
        # старт задержки ночью, окончание утром
        delay_start3 = datetime.datetime.fromisoformat('2020-04-10 07:20:34.123456')
        delay_finish3 = get_delay_time(delay_start3, 180.0, 30)

        self.assertEqual(datetime.datetime.fromisoformat('2020-04-10 09:00:00'), delay_finish1)
        self.assertEqual(datetime.datetime.fromisoformat('2020-04-10 09:00:00'), delay_finish2)
        self.assertEqual(datetime.datetime.fromisoformat('2020-04-10 10:30:00'), delay_finish3)

    @patch('app.IncartDateTime.get_night_start')
    @patch('app.IncartDateTime.get_night_finish')
    def test_get_wait_time(self, mock_get_night_finish, mock_get_night_start):
        mock_get_night_start.return_value = datetime.time.fromisoformat('21:00:00')
        mock_get_night_finish.return_value = datetime.time.fromisoformat('09:00:00')

        start1 = datetime.datetime.fromisoformat(('2020-04-09 12:20:34.123'))
        finish1 = get_wait_time(start1, 120.0, 30)
        start2 = datetime.datetime.fromisoformat(('2020-04-09 19:20:34.123'))
        finish2 = get_wait_time(start2, 120.0, 30)

        self.assertEqual(datetime.datetime.fromisoformat('2020-04-09 14:30:00'), finish1)
        self.assertEqual(datetime.datetime.fromisoformat('2020-04-10 09:30:00'), finish2)


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
        jobdoctor.request_started = datetime.datetime.now().astimezone(datetime.timezone.utc)
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
        repo = Repo(dal.session)
        job = repo.get_incartjob('2')
        candidate: Doctor = repo.get_job_candidate(job)

        self.assertIsNotNone(candidate)
        self.assertTrue(isinstance(candidate, Doctor))
        self.assertEqual(candidate.id, 1)

    # возврат None если все докторы отказались
    def test_get_job_none_candidate(self):
        repo = Repo(dal.session)
        doc3: Doctor = repo.get_doctor(id=96881373)  # Eugeny Bobylev
        doc3.is_active = False  # временно не доступен (temporarily unavailable)
        job: IncartJob = repo.get_incartjob(id="1")  # у этого задания есть 2 обращения к док 1 и 2
        doctor: Doctor = repo.get_job_candidate(job)

        self.assertIsNone(doctor)

    def test_get_all_unclosing_jobs(self):
        all_jobs = dal.session.query(IncartJob).all()
        jobs = dal.session.query(IncartJob).filter(IncartJob.closed.is_(None)).all()
        self.assertEqual(len(jobs), len(all_jobs))

    def test_repo_get_unclosing_jobs(self):
        repo = Repo(dal.session)
        jobs: List[IncartJob] = repo.get_unclosing_jobs()
        all_jobs = dal.session.query(IncartJob).all()
        self.assertTrue(len(jobs), len(all_jobs))


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
    job_doctor2.request_sended = datetime.datetime.utcnow()
    session.add(job_doctor2)
    session.commit()


if __name__ == '__main__':
    unittest.main()
