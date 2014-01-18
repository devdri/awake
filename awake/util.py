from Queue import Queue
from threading import Thread

class AsyncTask(object):
    def __init__(self):
        self.queue = Queue.Queue()
        self.thread = Thread(target=self.work)
        self.thread.daemon = True
        self.error = None
        self.started = False

    def start(self):
        self.started = True
        self.error = None
        self.thread.start()

    def isFinished(self):
        return self.started and not self.thread.is_alive()

    def work(self):
        queue.put("AsyncTask works.")
