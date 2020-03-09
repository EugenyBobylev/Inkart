import concurrent.futures
import logging
import threading
import time
import random

SENTINEL = object()


class Pipeline:
    """Class to allow a single element pipeline between producer and consumer.
    """
    def __init__(self):
        self.message = 0
        self.producer_lock = threading.Lock()
        self.consumer_lock = threading.Lock()
        self.consumer_lock.acquire()
        logging.debug("pipeline created")

    def get_message(self, name):
        if not self.consumer_lock.locked():
            logging.debug("%s:about to acquire getlock", name)
            self.consumer_lock.acquire()
        logging.debug("%s:have getlock", name)
        message = self.message
        if self.producer_lock.locked():
            logging.debug("%s:about to release setlock", name)
            self.producer_lock.release()
            logging.debug("%s:setlock released", name)
        return message

    def set_message(self, message, name):
        if not self.consumer_lock.locked():
            logging.debug("%s:about to acquire setlock", name)
            self.producer_lock.acquire()
            logging.debug("%s:have setlock", name)
        self.message = message
        if self.consumer_lock.locked():
            logging.debug("%s:about to release getlock", name)
            self.consumer_lock.release()
            logging.debug("%s:getlock released", name)


def producer(pipeline):
    """Pretend we're getting a message from the network."""
    for index in range(10):
        message: int = random.randint(1, 101)
        logging.debug(f"={message}")
        logging.info("Producer got message: %s", message)
        pipeline.set_message(message, "Producer")
    # Send a sentinel message to tell consumer we're done
    pipeline.set_message(SENTINEL, "Producer")


def consumer(pipeline):
    """ Pretend we're saving a number in the database. """
    message = 0
    while message is not SENTINEL:
        message = pipeline.get_message("Consumer")
        if message is not SENTINEL:
            logging.info("Consumer storing message: %s", message)


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    # logging.basicConfig(filename='sample.log', filemode='w', format=format, level=logging.INFO, datefmt="%H:%M:%S")
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
    pipeline = Pipeline()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(producer, pipeline)
        executor.submit(consumer, pipeline)
        time.sleep(10)
