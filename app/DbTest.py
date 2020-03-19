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


def add_job(id: str) -> None:
    job: IncartJob = IncartJob()
    job.id = id
    job.snippet = 'test job'
    dal.session.add(job)
    dal.session.commit()
    print(f'{job.id=}; {job.snippet=}; {job.candidate_id=}; {job.doctor_id=}')
    dal.session.close()
    print(f'{job.id=}; {job.snippet=}; {job.candidate_id=}; {job.doctor_id=}')
    print('job added successful')


if __name__ == "__main__":
    dal.connect()
    add_job('9876543210')

    #job_id = '987654321'
    #t: Thread = Thread(target=print_job, args=(job_id,))
    #t.start()
    #t.join()
    print("exit")

