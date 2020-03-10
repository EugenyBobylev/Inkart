import pytest

from app.Job import JobStatus
from app.model import InkartJob


def test_true():
    assert True


def test_inkart_job():
    job = InkartJob()
    assert job.status == JobStatus.CREATED


def test_gmail_message():
    assert True
