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
from rec import Rec
from cls import Cls

from bson import ObjectId
 
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

def 

def job_feed():
	try:
		feeds.run()
	except Exception, e:
		print e

def job_updateUPre():
	try:
		transport = TSocket.TSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Rec.Client(protocol)
		transport.open()
		for u in db.user.find() 
			print client.updateUPre(str(u['_id']))
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateRList():
	try:
		transport = TSocket.TSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Rec.Client(protocol)
		transport.open()
		for u in db.user.find() 
			client.updateRList(str(u['_id']))
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
			client.updateLsiIndex(c)
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateLsiDic():
	try:
		transport = TSocket.TSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Rec.Client(protocol)
		transport.open()
		for c in cs 
			client.updateLsiDic(c)
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_updateClassifyDic():
	try:
		transport = TSocket.TSocket(PARAMS['classify']['ip'], PARAMS['classify']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Cls.Client(protocol)
		transport.open()
		client.updateClassifyDic()
		transport.close()	 
	except Thrift.TException, ex:
		print "%s" % (ex.message)

def job_trainClassify():
	try:
		transport = TSocket.TSocket(PARAMS['classify']['ip'], PARAMS['classify']['port'])
		transport = TTransport.TBufferedTransport(transport)
		protocol = TBinaryProtocol.TBinaryProtocol(transport)
		client = Cls.Client(protocol)
		transport.open()
		client.trainClassify(str(u['_id']))
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
		import pymongo
		conn_primary = pymongo.Connection(PARAMS['db_primary']['ip'])
		db = conn_primary['feed']
		db.authenticate(PARAMS['db_primary']['username'], PARAMS['db_primary']['password'])

		for j in db.job.find({'starttime':{'$lt':datetime.datetime.now()}, \
				'status':'waiting'}, timeout=False):
			try:
				db.job.update({'_id':j['_id']}, {'$set':{'status':'running'}})
				exec( j['module'] + '.run()' )
				db.job.remove({'_id':j['_id']})
			except Exception, e:
				db.job.update({'_id':j['_id']}, {'$set':{'status':'failed'}})
				print j['module'] + str(e)
		conn.close()
		time.sleep(60 * 15)