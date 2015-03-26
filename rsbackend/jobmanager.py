# -*- coding: utf-8 -*-

import time, datetime
import feeds
import json
import sys

PARAMS_DIR = '../self.cfg'
PARAMS = json.load(file(PARAMS_DIR))
sys.path.append(PARAMS['thrift']['gen-py'])

cs = json.load(file(PARAMS['category']))

from search import Search
# from search.ttypes import *
from rec import Rec
# from rec.ttypes import *
from cls import Cls
# from cls.ttypes import *
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

def job_feed():
	db.job.insert({'function':'job_feed', \
		'starttime':now() + datetime.timedelta(hours=12), 'status':'waiting'})
	feeds.run()
	db.job.insert({'function':'job_updateLsiIndex', \
		'starttime':now() + datetime.timedelta(minutes=17), 'status':'waiting'})
	db.job.insert({'function':'job_updateSearchIndex', \
		'starttime':now() + datetime.timedelta(minutes=37), 'status':'waiting'})
	db.job.insert({'function':'job_classify', \
		'starttime':now() + datetime.timedelta(minutes=52), 'status':'waiting'})

def job_updateUPre():
	db.job.insert({'function':'job_updateUPre', \
		'starttime':now() + datetime.timedelta(hours=24), 'status':'waiting'})
	try:
		transport = TSocket.TSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Rec.Client(protocol)
		transport.open()
		for u in db.user.find() 
			client.updateUPre(str(u['_id']))
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateRList():
	db.job.insert({'function':'job_updateRList', \
		'starttime':now() + datetime.timedelta(minutes=58), 'status':'waiting'})
	try:
		transport = TSocket.TSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Rec.Client(protocol)
		transport.open()
		for u in db.user.find() 
			try:
				client.updateRList(str(u['_id']))
			except Exception, e:
				print e
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateLsiIndex():
	try:
		transport = TSocket.TSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Rec.Client(protocol)
		transport.open()
		for c in cs 
			try:
				client.updateLsiIndex(c)
			except Exception, e:
				print e
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateLsiDic():
	db.job.insert({'function':'job_updateLsiDic', \
		'starttime':now() + datetime.timedelta(days=5), 'status':'waiting'})
	try:
		transport = TSocket.TSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Rec.Client(protocol)
		transport.open()
		for c in cs 
			try:
				client.updateLsiDic(c)
			except Exception, e:
				print e
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateClassifyDic():
	db.job.insert({'function':'job_updateClassifyDic', \
		'starttime':now() + datetime.timedelta(days=15), 'status':'waiting'})
	try:
		transport = TSocket.TSocket(PARAMS['classify']['ip'], PARAMS['classify']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Cls.Client(protocol)
		transport.open()
		client.updateClassifyDic()
		transport.close()	 
		db.job.insert({'function':'job_updateClassifyDic', \
			'starttime':now() + datetime.timedelta(minutes=13), 'status':'waiting'})
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_trainClassify():
	db.job.insert({'function':'job_updateClassifyDic', \
		'starttime':now() + datetime.timedelta(days=10), 'status':'waiting'})
	try:
		transport = TSocket.TSocket(PARAMS['classify']['ip'], PARAMS['classify']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Cls.Client(protocol)
		transport.open()
		client.trainClassify()
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_classify():
	try:
		transport = TSocket.TSocket(PARAMS['classify']['ip'], PARAMS['classify']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Cls.Client(protocol)
		transport.open()
		client.classify('综合')
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateSearchIndex():
	try:
		transport = TSocket.TSocket(PARAMS['search']['ip'], PARAMS['search']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Search.Client(protocol)
		transport.open()
		client.updateSearchIndex()
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

if __name__ == '__main__':
	while True:
		for j in db.job.find({'starttime':{'$lt':datetime.datetime.now()}, \
				'status':'waiting'}, timeout=False):
			try:
				db.job.update({'_id':j['_id']}, {'$set':{'status':'running'}})
				exec( j['function'] + '()' )
				db.job.update({'_id':j['_id']}, {'$set':{'status':'completed'}})
			except Exception, e:
				db.job.update({'_id':j['_id']}, {'$set':{'status':'failed'}})
				print j['module'] + str(e)
		conn.close()
		time.sleep(60 * 15)