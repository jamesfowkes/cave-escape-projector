import threading
import queue

import logging
import logging.handlers

import time
import requests

import serial

SCAN_TIME = 0.5

def get_logger():
    return logging.getLogger(__name__)

def strip_quotes(s):
    if s[0] == "'":
        s = s[1:]

    if s[-1] == "'":
        s = s[0:-1]

    return s


class RAATCardReader(threading.Thread):

    def __init__(self, device="/dev/ttyUSB0", **kwargs):
        super(RAATCardReader, self).__init__()
        self.queue = kwargs.get("queue", None)
        self.url = kwargs.get("url", None)
        self.device = device
        self.reader = serial.Serial(device, 115200, timeout=1)
        time.sleep(2)
        self.runflag = True
        self.last_reply = ""

    def read(self):
        self.reader.write("/param/01/?\r\n".encode())
        reply = self.reader.readline().decode("ascii").strip()
        return reply

    def run(self):

        while self.runflag:
            reply = strip_quotes(self.read())

            if reply != self.last_reply:
                self.last_reply = reply
                uid = reply
                if len(uid):
                    get_logger().info("Reader got UID {}".format(uid))
                    if self.queue:
                        get_logger().info("Putting on queue.")
                        self.queue.put(uid)
                    if self.url:
                        full_url = self.url.format(uid=uid)
                        get_logger().info("Posting to URL {}".format(full_url))
                        try:
                    	    requests.get(full_url, timeout=1)
                        except requests.exceptions.ConnectionError:
                            get_logger().info("Connection error when opening {}".format(full_url))
                        except requests.exceptions.Timeout:
                            get_logger().info("Timeout when opening {}".format(full_url))

            time.sleep(SCAN_TIME)

    def stop(self):
        self.runflag = False

def setup_logging(handler):
    get_logger().setLevel(logging.INFO)
    get_logger().addHandler(handler)

if __name__ == "__main__":

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging_handler = logging.handlers.RotatingFileHandler("cardreader.log", maxBytes=1024*1024, backupCount=3)
    logging_handler.setFormatter(formatter)
    get_logger().setLevel(logging.INFO)
    get_logger().addHandler(logging_handler)

    reader_queue = queue.Queue()
    reader = RAATCardReader(queue=reader_queue)

    reader.start()

    while True:
        try:
            uid = reader_queue.get(False)
            print("New UID: {}".format(uid))
        except queue.Empty:
            pass
        except KeyboardInterrupt:
            break

    reader.stop()
    reader.join()
