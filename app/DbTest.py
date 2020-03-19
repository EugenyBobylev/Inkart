from threading import Thread
from datetime import datetime

from app.model import dal, IncartJob, Doctor, DataAccessLayer


def print_job(job_id: str):
    with dal.session_scope() as session:
        job: IncartJob = session.query(IncartJob).filter(IncartJob.id == job_id).first()
        job.candidate_id = 12345
        job.doctor_id = 12345
        session.add(job)
        session.rollback()
        if job is not None:
            print(f'{job.id=}; {job.snippet=}; {job.candidate_id=}; {job.doctor_id=}')
        else:
            print("job is None")


def print_job_v2(job: IncartJob):
    with dal.session_scope() as session:
        job.candidate_id = 12345
        job.doctor_id = 12345
        session.add(job)
        print(f'{job.id=}; {job.snippet=}; {job.candidate_id=}; {job.doctor_id=}')


def add_job(id: str) -> IncartJob:
    job: IncartJob = create_job()
    # job.id = id
    # job.snippet = 'test job'
    dal.session.add(job)
    dal.session.commit()
    dal.session.close()
    print('job added successful')
    return job

def create_job() -> IncartJob:
    job: IncartJob = IncartJob()
    job.id = '170c3a9ba451cd9e'
    job.snippet = "Задание на обработку"
    job.request_id = 367024826
    job.request_started = datetime.strptime('2020-03-19 05:04:11.614537+00:00', '%Y-%m-%d %H:%M:%S.%f%z')
    job.request_time_estimate = datetime.strptime('2020-03-19 06:04:11.614537+00:00', '%Y-%m-%d %H:%M:%S.%f%z')
    job.request_answer_id = 367025803
    job.answered = datetime.strptime('2020-03-19 05:06:20+00:00', '%Y-%m-%d %H:%M:%S%z')
    job.doctor_id = 96881373
    job.job_start_id = 367025903
    job.job_started = datetime.strptime('2020-03-19 05:06:21.049030+00:00', '%Y-%m-%d %H:%M:%S.%f%z')
    job.job_time_estimate = datetime.strptime('2020-03-19 07:16:21.049030+00:00', '%Y-%m-%d %H:%M:%S.%f%z')
    job.job_finish_id = 367026544
    job.job_finished = datetime.strptime('2020-03-19T05:08:10 UTC', '%Y-%m-%dT%H:%M:%S %Z')
    job.closed = datetime.strptime('2020-03-19 05:08:28.094666+00:00', '%Y-%m-%d %H:%M:%S.%f%z')
    return job


if __name__ == "__main__":
    dal.connect()
    job = add_job('9876543210')
    # job = create_job()
    print(job)

    #job_id = '987654321'
    # t: Thread = Thread(target=print_job_v2, args=(job,))
    # t.start()
    # t.join()
    print("exit")

