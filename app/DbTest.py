from threading import Thread

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
    job: IncartJob = IncartJob()
    job.id = id
    job.snippet = 'test job'
    dal.session.add(job)
    dal.session.commit()
    dal.session.close()
    print(f'{job.id=}; {job.snippet=}; {job.candidate_id=}; {job.doctor_id=}')
    print('job added successful')
    return job


if __name__ == "__main__":
    dal.connect()
    job = add_job('9876543210')

    #job_id = '987654321'
    t: Thread = Thread(target=print_job_v2, args=(job,))
    t.start()
    t.join()
    print("exit")

