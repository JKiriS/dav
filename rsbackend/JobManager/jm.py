# -*- coding: utf-8 -*-

from bson import ObjectId
from datetime import datetime, timedelta
import time
import traceback
from threading import Thread
import sys, os
import pickle
import pymongo

sys.path.append(os.path.join(os.path.dirname(__file__), 'gen-py'))

from jobmanager import JM

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

now = lambda : datetime.utcnow()

class JobManager(object):
    def __new__(cls, *args, **kwargs):
        if not '_object' in cls.__dict__:
            cls._object = object.__new__(cls, *args, **kwargs)
        return cls._object

    def __init__(self, port=9093, host='0.0.0.0'):
        self._tasks = []
        self._funcs = {}
        self.host, self.port = host, port
        self._db = None

    def connectdb(self, username, password, host='localhost'):
        conn = pymongo.Connection(host)
        self._db = conn['feed']
        self._db.authenticate(username, password)

    def task(self, func):
        if func.__name__ in self._funcs:
            raise Exception('func "{}" duplicated'.format(func.__name__))
        self._funcs[func.__name__] = func
        def _inn(*args, **kwargs):
            if 'delay' in kwargs:
                if not isinstance(kwargs['delay'], int):
                    raise Exception('delay not integer')
                starttime = now() + timedelta(seconds=kwargs['delay'])
                kwargs.pop('delay')
            else:
                starttime = now()
            if 'interval' in kwargs:
                if not isinstance(kwargs['interval'], int):
                    raise Exception('interval not integer')
                interval = seconds=kwargs['interval']
                kwargs.pop('interval')
            else:
                interval = None
            task = self._newTask(func.__name__, args, kwargs, starttime, interval)

            transport = TSocket.TSocket(self.host, self.port)
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = JM.Client(protocol)
            transport.open()
            client.addTask(pickle.dumps(task))
        return _inn

    def addTask(self, task_str):
        try:
            task = pickle.loads(task_str)
            self._addTask(task)
            return True
        except Exception, e:
            print e
            return False

    def _addTask(self, task):
        for i, t in enumerate(self._tasks):
            if task['starttime'] >= t['starttime']:
                self._tasks.insert(i, task)
                break
        else:
            self._tasks.append(task)
        self._saveTask(task)
        return task

    def _newTask(self, funcname, args, kwargs, starttime, interval):
        task = {'id':ObjectId()}
        task['func'] = funcname
        task['args'] = args
        task['kwargs'] = kwargs
        task['starttime'] = starttime
        task['interval'] = interval
        task['status'] = 'waiting'
        return task

    def _saveTask(self, task):
        if self._db:
            try:
                self._db.job.save(task)
            except Exception, e:
                print e

    def _loadTask(self):
        if self._db:
            for task in self._db.job.find({'status':'waiting'}):
                self._addTask(task)

    def _run(self):
        while True:
            if self._tasks and self._tasks[-1]['starttime'] <= now():
                task = self._tasks.pop()
                try:
                    task['status'] = 'running'
                    self._saveTask(task)
                    self._funcs[task['func']](*task['args'], **task['kwargs'])
                    task['status'] = 'completed'
                except Exception, e:
                    print traceback.format_exc()
                    task['status'] = 'failed'
                    task['info'] = str(traceback.format_exc())
                else:
                    if task['interval']:
                        newtask = self._newTask(task['func'], task['args'], task['kwargs'],
                            now() + timedelta(seconds=task['interval']), task['interval'])
                        self._addTask(newtask)
                finally:
                    self._saveTask(task)
            time.sleep(3)

    def run(self):
        self._loadTask()
        t = Thread(target=self._run)
        t.setDaemon(True)
        t.start()
        processor = JM.Processor(self)
        transport = TSocket.TServerSocket(self.host, self.port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
        server.serve()
