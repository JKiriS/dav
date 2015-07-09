﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import os, sys, getopt

# opts, args = getopt.getopt(sys.argv[1:], "f:")
# if len(opts) == 0:
# 	exit()
# PARAMS_DIR = opts[0][1]
# sys.argv.remove(opts[0][0])
# sys.argv.remove(opts[0][1])
# if not os.path.isfile(PARAMS_DIR):
# 	PARAMS_DIR = "e:/dav/self.cfg"
PARAMS_DIR = "e:/dav/self.cfg"
import json
PARAMS = json.load(file(PARAMS_DIR))
sys.path.append(PARAMS['thrift']['gen-py'])

from cls import Cls
from common.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

import logging
import logging.config
logging.config.fileConfig(PARAMS['logger']['python'])
logger = logging.getLogger("thrift")

import jieba
stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') \
	for line in open(PARAMS['jieba']['stopwords']) ])
stopwords[' '] = 1
stopwords['.'] = 1
logger.info('jieba and stopwords load success')

cs = json.load(file(PARAMS['category']))
CLS_DIR = PARAMS['classify']['dir']
LSI_DIR = PARAMS['recommend']['dir']
now = lambda:datetime.datetime.utcnow()

import pymongo
class DBManager:
	def __init__(self):
		self._db_local = None
		self._db_primary = None

	def getlocal(self):
		if self._db_local is None:
			self._conn_local = pymongo.Connection(PARAMS['db_local']['ip'])
			self._db_local = self._conn_local['feed']
			self._db_local.authenticate(PARAMS['db_local']['username'], PARAMS['db_local']['password'])
			logger.info('local mongodb connection success')
		return self._db_local

	def getprimary(self):
		if self._db_primary is None:
			self._conn_primary = pymongo.Connection(PARAMS['db_primary']['ip'])
			self._db_primary = self._conn_primary['feed']
			self._db_primary.authenticate(PARAMS['db_primary']['username'], PARAMS['db_primary']['password'])
			logger.info('primary connection success')
		return self._db_primary

dbm = DBManager()

from bson import ObjectId
import datetime, time
import math
import random
import pickle
import numpy as np
from gensim import corpora, models

class ClsFileManager:
	def __init__(self):
		self._dic = None
		self._model = None
		self._ids = None
	def _wait(self):
		for i in range(10):
			if os.path.isfile(os.path.join(CLS_DIR, 'write.lock')):
				time.sleep(10)
			if i == 9:
				ex = FileError()
				ex.who = os.path.join(CLS_DIR, 'write.lock')
				raise ex
			else:
				break
	def _lock(self):
		if os.path.isfile(os.path.join(CLS_DIR, 'write.lock')):
			return False
		else:
			flock = open(os.path.join(CLS_DIR, 'write.lock'),'w+')
			flock.close()
			return True
	def _clearlock(self):
		if os.path.isfile(os.path.join(CLS_DIR, 'write.lock')):
			os.remove(os.path.join(CLS_DIR, 'write.lock'))
	def getdic(self):
		if self._dic is None:
			self._wait()
			self._dic = corpora.Dictionary.load(os.path.join(CLS_DIR, 'cls.dic'))
		return self._dic
	def getmodel(self):
		if self._model is None:
			self._wait()
			self._model = pickle.load(open(os.path.join(CLS_DIR, 'cls.pkl'), 'rb'))
		return self._model
	def getid(self):
		if self._ids is None:
			self._wait()
			self._ids = pickle.load(open(os.path.join(CLS_DIR,'ids.pkl'), 'rb'))
		return self._ids
	def setdic(self, newdic):
		self._dic = newdic
		self._wait()
		self._lock()
		self._dic.save(os.path.join(CLS_DIR, 'cls.dic'))
		self._clearlock()	
		return True
	def setmodel(self, newmodel):
		self._model = newmodel
		self._wait()
		self._lock()
		pickle.dump(self._model, open(os.path.join(CLS_DIR, 'cls.pkl'), 'wb'))
		self._clearlock()
		return True
	def setid(self, newid):
		self._ids = newid
		self._wait()
		self._lock()
		pickle.dump(self._ids, open(os.path.join(CLS_DIR,'ids.pkl'), 'wb'))
		self._clearlock()
		return True
cfm = ClsFileManager()

class ClsHandler:
	def updateClassifyDic(self):
		logger.info('update classify dictionary')
		dic = None
		for c in cs:
			cpath = os.path.join(LSI_DIR, c)
			if dic is None:
				dic = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
			else:
				dic.merge_with(corpora.Dictionary.load(os.path.join(cpath,'gs.dic')))
		cfm.setdic(dic)
		res = Result()
		res.success = True
		return res

	def trainClassify(self):
		logger.info('train Classify model')
		dictionary = cfm.getdic()
		t = now() - datetime.timedelta(days=180)
		db = dbm.getlocal()
		itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
		texts_origin = []
		train_target = np.array([])
		for ix, c in enumerate(cs):
			itemnum_c = db.item.find({'category':c,'pubdate':{'$gt':t}}).count()
			readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))
			tnum_before = len(texts_origin)
			for i in db.item.find({'category':c}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
				segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
				segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
				texts_origin.append(segs)
			train_target = np.hstack(( train_target, np.zeros(len(texts_origin) - tnum_before) + ix ))
		if len(texts_origin) == 0:
			ex = DataError()
			ex.who = 'texts_origin'
			raise ex
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		corpus = [dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus)
		corpus_tfidf = tfidf[corpus]
		train_data = np.zeros([len(corpus_tfidf), len(dictionary)])	
		for ix, doc in enumerate(corpus_tfidf):
			for jx, d in doc:
				train_data[ix, jx] = d
		from sklearn.naive_bayes import MultinomialNB  
		clf = MultinomialNB(alpha = 0.01)   
		clf.fit(train_data, train_target)
		cfm.setmodel(clf)
		res = Result()
		res.success = True
		return res

	def classify(self, category):
		category = category.decode('utf-8') # chinese decode
		logger.info('classify items of category ' + category)
		dictionary = cfm.getdic()
		texts_origin = []
		ids = []
		db = dbm.getlocal()
		for i in db.item.find({'category':category, 'category_origin':None}).limit(200):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
			ids.append(i['_id'])
		if len(texts_origin) == 0 or len(texts_origin) != len(ids):
			ex = DataError()
			ex.who = 'texts_origin'
			raise ex
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		corpus = [dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus)
		corpus_tfidf = tfidf[corpus]
		test_data = np.zeros([len(corpus_tfidf), len(dictionary)])
		for ix, doc in enumerate(corpus_tfidf):
			for jx, d in doc:
				test_data[ix, jx] = d
		clf = cfm.getmodel()
		cfm.setid(ids)
		clears = {}
		unclears = {}
		for i, d in enumerate(clf.predict_proba(test_data)):
			res = sorted(enumerate(d), key=lambda a:a[1], reverse=True)
			if res[0][1] - res[1][1] < 0.15:
				top_prob = res[:3]
				random.shuffle(top_prob)
				unclears[ ids[i] ] = top_prob
			else:
				clears[res[0][0]] = clears.get(res[0][0], []) + [ ids[i] ]
		db_primary = dbm.getprimary()
		db_primary.item.update({"_id":{"$in":unclears.keys()}}, {"$set":{'category_origin':category}}, multi=True)
		for nc in clears:
			db_primary.item.update({"_id":{"$in":clears[nc]}}, {"$set":{'category':cs[nc], 'category_origin':category}}, multi=True)
		veris = []
		for uci in db.item.find({"_id":{"$in":unclears.keys()}}):
			question = u'''请问下面的内容最可能属于哪一类？<br/>
						标题: {0}<br/>
						正文: {1}
					'''.format(uci['title'], uci['des'])
			option = [ cs[o[0]] for o in unclears[uci['_id']] ] + [u'其他']
			veris.append({ '_id':uci['_id'], 'rand':[random.random(), 0], \
				'question':question, 'option':option, 'data_origin':{'id':uci['_id'], 'prob':uci['_id']} })
		db_primary.verification.insert(veris, continue_on_error=True)
		res = Result()
		res.success = True
		return res

import win32serviceutil
import win32service
import win32event

class clsserver(win32serviceutil.ServiceFramework):
	_svc_name_ = "ClsService"
	_svc_display_name_ = "classify service"
	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		# Create an event which we will use to wait on.
		# The "service stop" request will set this event.
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

	def SvcStop(self):
		# Before we do anything, tell the SCM we are starting the stop process.
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		# And set my event.
		win32event.SetEvent(self.hWaitStop)

	def SvcDoRun(self):
		# We do nothing other than wait to be stopped!
		handler = ClsHandler()
		processor = Cls.Processor(handler)
		transport = TSocket.TServerSocket(PARAMS['classify']['ip'], PARAMS['classify']['port'])
		tfactory = TTransport.TBufferedTransportFactory()
		pfactory = TBinaryProtocol.TBinaryProtocolFactory()
		 
		server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
		 
		logger.info("Starting classify service at port " + repr(PARAMS['classify']['port']) + " ...")
		server.serve()
		win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
	win32serviceutil.HandleCommandLine(clsserver)

