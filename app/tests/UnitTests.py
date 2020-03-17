import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timezone, timedelta

import app.model
import app.Job
from app.WhatsappChanel import get_api_message
from app.WhatsappNotification import confirm_request
from app.repo import Repo


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.job = app.model.IncartJob()
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


class RepoTests(unittest.TestCase):
    def test_get_all_doctors(self):
        repo = Repo()
        doctors = repo.get_all_doctors()

        self.assertTrue(len(doctors) > 0)

if __name__ == '__main__':
    unittest.main()
