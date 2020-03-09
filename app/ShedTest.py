import sched
import threading
import time

# Set up a global to be modified by the threads
counter = 0
scheduler = sched.scheduler(time.time, time.sleep)


def long_event(name):
    print(f'BEGIN EVENT: {time.time()} "{name}"')
    time.sleep(2)
    print(f'FINISH EVENT: {time.time()} "{name}"')


def print_event(name):
    print(f'EVENT: {time.time()} "{name}"')


def increment_counter(name):
    global counter
    print(f'EVENT: {time.time()} "{name}"')
    counter += 1
    print(f'NOW: {counter}')


def start_overlapping():
    print(f'START: {time.time()}')
    scheduler.enter(2, 1, long_event, ('first',))
    scheduler.enter(3, 1, long_event, ('second',))
    scheduler.run()


def start_canceling():
    print(f'START: {time.time()}', )
    e1 = scheduler.enter(2, 1, increment_counter, ('E1',))
    e2 = scheduler.enter(3, 1, increment_counter, ('E2',))

    # Start a thread to run the events
    t = threading.Thread(target=scheduler.run)
    t.start()
    # Back in the main thread, cancel the first scheduled event.
    scheduler.cancel(e2)
    # Wait for the scheduler to finish running in the thread
    t.join()

    print(f'FINAL: {counter}')


start_overlapping()
# start_canceling()
