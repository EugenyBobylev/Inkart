import time
from timeloop import Timeloop
from datetime import timedelta

tl = Timeloop()


@tl.job(interval=timedelta(seconds=5))
def check_new_email():
    print("You have no new email messages")


if __name__ == "__main__":
    tl.start(block=True)