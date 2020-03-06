import time
from timeloop import Timeloop
from datetime import timedelta

tl = Timeloop()


@tl.job(interval=timedelta(seconds=2))
def sample_job_every_2s():
    print("2s job current time : {}".format(time.ctime()))


@tl.job(interval=timedelta(seconds=5))
def sample_job_every_5s():
    print("5s job current time : {}".format(time.ctime()))


@tl.job(interval=timedelta(seconds=10))
def sample_job_every_10s():
    print("10s job current time : {}".format(time.ctime()))


if __name__ == "__main__":
    tl.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            tl.stop()
