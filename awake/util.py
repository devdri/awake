from Queue import Queue
from threading import Thread
import Tkinter as tk
import ttk

tk_root = None

def getTkRoot():
    global tk_root
    if not tk_root:
        tk_root = tk.Tk()
        tk_root.withdraw()
    return tk_root

class AsyncTask(object):
    def __init__(self):
        self.queue = Queue()
        self.thread = None
        self.error = None
        self.requestCancel = False

    def start(self):
        if self.thread:
            if not self.isFinished():
                print 'Warning: previous task not finished yet.'
            self.thread = None
        self.error = None
        self.requestCancel = False
        self.thread = Thread(target=self.work)
        self.thread.daemon = True
        self.thread.start()

    def isFinished(self):
        return self.thread is not None and not self.thread.is_alive()

    def executeSynchronous(self):
        self.requestCancel = False
        self.error = None
        self.work()

    def report(self, *args):
        self.queue.put(args)

    def work(self):
        queue.put("AsyncTask works.")

class RadioGroup(ttk.LabelFrame):
    def __init__(self, parent, text, options, default=None):
        ttk.LabelFrame.__init__(self, parent, text=text)

        self.var = tk.StringVar()
        if default:
            self.var.set(default)

        for text, value in options:
            radio = ttk.Radiobutton(self, text=text, variable=self.var, value=value)
            radio.pack(side='top', fill='x')

    def getValue(self):
        return self.var.get()

class BankSelect(ttk.Combobox):
    def __init__(self, parent, proj, includeAny=False):
        num_banks = proj.rom.numBanks()
        banks = [('Bank {:02X}'.format(x), x) for x in range(num_banks)]
        self.textToBank = dict(banks)
        values = [x[0] for x in banks]
        self.var = tk.StringVar()
        self.var.set(values[0])
        ttk.Combobox.__init__(self, parent, state='readonly', textvariable=self.var, values=values, width=10)

    def getValue(self):
        return self.textToBank[self.var.get()]
