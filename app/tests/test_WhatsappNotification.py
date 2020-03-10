import pytest

from app.Job import JobStatus
from app.WhatsappNotification import find_doctor
from app.model import InkartJob


@pytest.fixture
def my_job():

    whatsapp_data = {'message_id': 360611360, 'channel_id': 19286, 'operator_id': 59750, 'transport': 'whatsapp',
                     'type': 'to_client', 'client_id': 96881373, 'dialog_id': 12667967, 'request_id': 43678558}
    job = InkartJob.from_js
    return  job

def test_find_doctor(my_job):
    assert my_job.status == JobStatus.CREATED
