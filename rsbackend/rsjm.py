# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import json
import feeds
import sys, os
from JobManager import JobManager

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PARAMS_DIR = os.path.join(BASE_DIR,'self.cfg')
PARAMS = json.load(file(PARAMS_DIR))
sys.path.append(PARAMS['thrift']['gen-py'])

now = lambda : datetime.utcnow()

from rec import Rec
from cls import Cls
from search import Search
from common.ttypes import *

from bson import ObjectId

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

import pymongo
conn_primary = pymongo.Connection(PARAMS['db_primary']['ip'])
db = conn_primary['feed']
db.authenticate(PARAMS['db_primary']['username'], PARAMS['db_primary']['password'])

cs = [c['name'] for c in db.category.find()]


jobm = JobManager(PARAMS['jobmanager']['port'], PARAMS['jobmanager']['ip'])

class ThriftConn(object):
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.transport = None

    def __enter__(self):
        self.transport = TSocket.TSocket(self.host, self.port)
        self.transport = TTransport.TBufferedTransport(self.transport)
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        client = self._client()
        self.transport.open()
        return client

    def __exit__(self, type, value, tb):
        if self.transport:
            self.transport.close()

    def _bindmethods(self):
        for i in dir(self.client):
            if not i.startswith('__'):
                setattr(self, i, getattr(self.client, i))

    def _client(self):
        return None

class SearchConn(ThriftConn):
    def __init__(self):
        ThriftConn.__init__(self, PARAMS['search']['ip'], PARAMS['search']['port'])

    def _client(self):
        return Search.Client(self.protocol)

class ClsConn(ThriftConn):
    def __init__(self):
        ThriftConn.__init__(self, PARAMS['classify']['ip'], PARAMS['classify']['port'])

    def _client(self):
        return Cls.Client(self.protocol)

class RecConn(ThriftConn):
    def __init__(self):
        ThriftConn.__init__(self, PARAMS['recommend']['ip'], PARAMS['recommend']['port'])

    def _client(self):
        return Rec.Client(self.protocol)

@jobm.task
def feed():
    feeds.run()
    updateLsiIndex(delay=17*60)
    updateLsiSearchIndex(delay=29*60)
    updateSearchIndex(delay=37*60)
    classify(delay=52*60)

@jobm.task
def updateUPre():
    with RecConn() as client:
        for u in db.user.find():
            client.updateUPre(str(u['_id']))

@jobm.task
def updateRList():
    with RecConn() as client:
        for u in db.user.find():
            client.updateRList(str(u['_id']))

@jobm.task
def updateLsiSearchDic():
    with RecConn() as client:
        client.updateLsiSearchDic()

@jobm.task
def updateLsiSearchIndex():
    with RecConn() as client:
        client.updateLsiSearchIndex()

@jobm.task
def updateLsiIndex():
    with RecConn() as client:
        for c in cs:
            client.updateLsiIndex(c.encode('utf-8'))

@jobm.task
def updateLsiDic():
    with RecConn() as client:
        for c in cs:
            client.updateLsiDic(c.encode('utf-8'))

@jobm.task
def updateClassifyDic():
    with ClsConn() as client:
        client.updateClassifyDic()
    trainClassifyModel(delay=13*60)

@jobm.task
def trainClassifyModel():
    with ClsConn() as client:
        client.trainClassify()

@jobm.task
def classify():
    with ClsConn() as client:
        client.classify('综合')

@jobm.task
def updateSearchIndex():
    with SearchConn() as client:
        client.updateSearchIndex()

if __name__ == '__main__':
    jobm.connectdb(PARAMS['db_primary']['username'], PARAMS['db_primary']['password'], PARAMS['db_primary']['ip'])
    jobm.run()