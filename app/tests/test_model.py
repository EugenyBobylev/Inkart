import pytest

from app.Job import JobStatus
from app.model import InkartJob


def test_true():
    assert True


def test_inkart_job_from_dict():
    dict = {"id": "170bbd4e9f709b1f", "snippet": "Тест для проверки"}
    job = InkartJob.from_json(dict)

    assert job.status == JobStatus.CREATED
    assert job.id == '170bbd4e9f709b1f'
    assert job.snippet == 'Тест для проверки'
    assert job.created is not None


def test_gmail_message():
    assert True
