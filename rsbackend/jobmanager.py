# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import json
import feeds
import sys, os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PARAMS_DIR = os.path.join(BASE_DIR,'self.cfg')
PARAMS = json.load(file(PARAMS_DIR))
sys.path.append(PARAMS['thrift']['gen-py'])

now = lambda : datetime.utcnow()
cs = json.load(file(PARAMS['category']))

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

class Job:
    def __init__(self, stime, jid, status='waiting'):
        self.name = self.__class__.__name__
        if isinstance(stime, timedelta):
            self.timestamp = time.mktime((now() + stime).timetuple())
        elif isinstance(stime, float):
            self.timestamp = stime
        if not jid:
            jid = ObjectId()
        self.starttime = datetime.fromtimestamp(self.timestamp)
        self.status = status
        self.id = jid
    def save(self):
        db.job.save({'_id':self.id,'name':self.name,'runable':self._cmd(),
                     'starttime':self.starttime,'status':self.status})
    def _cmd(self):
        return '{}({},ObjectId("{}")).run()' \
            .format(self.name,self.timestamp,self.id)

class Feed(Job):
    def __init__(self, stime, jid=None):
        Job.__init__(self, stime, jid)
    def run(self):
        reload(feeds)
        Feed(timedelta(hours=12)).save()
        try:
            db.job.update({'_id':self.id},{'$set':{'status':'running'}})
            feeds.run()
            db.job.update({'_id':self.id},{'$set':{'status':'completed'}})
        except Exception, e:
            db.job.update({'_id':self.id},{'$set':{'status':'failed'}})
            print e
        UpdateLsiIndex(timedelta(minutes=17)).save()
        UpdateSearchIndex(timedelta(minutes=37)).save()
        Classify(timedelta(minutes=52)).save()

def rundeco(func):
    def _deco(self, *args, **argv):
        self._connect()
        try:
            db.job.update({'_id':self.id},{'$set':{'status':'running'}})
            func(self, *args, **argv)
            db.job.update({'_id':self.id},{'$set':{'status':'completed'}})
        except Exception, e:
            print e
            db.job.update({'_id':self.id},{'$set':{'status':'failed'}})
        self._transport.close()
    return _deco

class ThriftJob(Job):
    def __init__(self, service, stime, jid):
        Job.__init__(self, stime, jid)
        self._service = service
    def _connect(self):
        self._transport = TSocket.TSocket(PARAMS[self._service]['ip'], PARAMS[self._service]['port'])
        self._transport = TTransport.TBufferedTransport(self._transport)
        self._protocol = TBinaryProtocol.TBinaryProtocol(self._transport)
        if self._service == 'recommend':
            self._client = Rec.Client(self._protocol)
        elif self._service == 'classify':
            self._client = Cls.Client(self._protocol)
        elif self._service == 'search':
            self._client = Search.Client(self._protocol)
        self._transport.open()

class UpdateUPre(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'recommend', stime, jid)
    @rundeco
    def run(self):
        UpdateUPre(timedelta(hours=24)).save()
        for u in db.user.find():
            try:
                self._client.updateUPre(str(u['_id']))
            except Exception, e:
                print e

class UpdateRList(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'recommend', stime, jid)
    @rundeco
    def run(self):
        UpdateRList(timedelta(hours=3)).save()
        for u in db.user.find():
            try:
                self._client.updateRList(str(u['_id']))
            except Exception, e:
                print e

class UpdateLsiIndex(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'recommend', stime, jid)
    @rundeco
    def run(self):
        for c in cs:
            try:
                self._client.updateLsiIndex(c.encode('utf-8'))
            except Exception, e:
                print e

class UpdateLsiDic(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'recommend', stime, jid)
    @rundeco
    def run(self):
        UpdateLsiDic(timedelta(days=5)).save()
        for c in cs:
            try:
                self._client.updateLsiDic(c.encode('utf-8'))
            except Exception, e:
                print e

class UpdateClassifyDic(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'classify', stime, jid)
    @rundeco
    def run(self):
        UpdateClassifyDic(timedelta(days=15)).save()
        self._client.updateClassifyDic()
        TrainClassifyModel(timedelta(minutes=13))

class TrainClassifyModel(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'classify', stime, jid)
    @rundeco
    def run(self):
        self._client.trainClassify()

class Classify(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'classify', stime, jid)
    @rundeco
    def run(self):
        self._client.classify('综合')

class UpdateSearchIndex(ThriftJob):
    def __init__(self, stime, jid=None):
        ThriftJob.__init__(self, 'search', stime, jid)
    @rundeco
    def run(self):
        self._client.updateSearchIndex()

if __name__ == '__main__':
    while True:
        for j in db.job.find({'starttime':{'$lt':now()}, 'status':'waiting'} \
                , timeout=False).sort('starttime',pymongo.ASCENDING):
            exec( j['runable'] )
        time.sleep(60 * 1)
	