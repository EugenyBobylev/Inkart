import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timezone, timedelta

from sqlalchemy import orm

from app.WhatsappChanel import get_api_message
from app.WhatsappNotification import confirm_request
from app.model import dal, IncartJob, Doctor, DataAccessLayer
from app.repo import Repo
from config import Config

class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.job = IncartJob()
        self.job.id = '170c3a9ba451cd9e'
        self.job.snippet = 'Задание на обработку № 123'

    def test_inсart_job(self):
        self.assertEqual('170c3a9ba451cd9e', self.job.id)
        self.assertEqual('Задание на обработку № 123', self.job.snippet)

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
        confirm_request(job=self.job, candidat_id=1)
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

class RepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        dal.conn_string = 'sqlite:///:memory:'
        dal.connect()
        prep_dal(dal.Session())

    def setUp(self) -> None:
        dal.session = dal.Session()

    def tearDown(self) -> None:
        dal.session.close()

    def test_get_doctor(self):
        repo = Repo(dal.session)
        doctor = repo.get_doctor(id=100)

        self.assertIsNotNone(doctor)
        self.assertTrue(doctor.id, 100)

    def test_get_all_doctors(self):
        repo = Repo(dal.session)
        doctors = repo.get_all_doctors()
        self.assertEquals(len(doctors), 1)

    def test_get_nonexist_doctor(self):
        repo = Repo(dal.session)
        doctor = repo.get_doctor(id=-20000)
        self.assertIsNone(doctor)

    def test_get_job(self):
        repo = Repo(dal.session)
        job = repo.get_incartjob(id='1234567890')
        self.assertIsNotNone(job)

    def test_add_job(self):
        job: IncartJob = IncartJob()
        job.id = '0987654321'
        job.snippet = 'test job'
        repo = Repo(dal.session)
        result = repo.add_incartjob(job)
        self.assertTrue(result["ok"])


# подготовка тестовой БД
def prep_dal(session: orm.session.Session):
    doctor = Doctor(id=100, name='test doctor')
    session.add(doctor)

    job: IncartJob = IncartJob()
    job.id = '1234567890'
    job.snippet = 'test job'
    session.add(job)

    session.commit()


if __name__ == '__main__':
    unittest.main()
