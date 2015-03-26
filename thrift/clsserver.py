#!/usr/bin/env python
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
from cls.ttypes import *

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
logger.info('stopwords load success')

cs = json.load(file(PARAMS['category']))
CLS_DIR = PARAMS['classify']['dir']

import pymongo
conn_local = pymongo.Connection(PARAMS['db_local']['ip'])
db_local = conn_local['feed']
db_local.authenticate(PARAMS['db_local']['username'], PARAMS['db_local']['password'])
conn_primary = pymongo.Connection(PARAMS['db_primary']['ip'])
db_primary = conn_primary['feed']
db_primary.authenticate(PARAMS['db_primary']['username'], PARAMS['db_primary']['password'])
logger.info('mongodb connection success')

from bson import ObjectId
import datetime
import math
import random
import pickle
import numpy as np
from gensim import corpora, models

class ClsHandler:
	def updateClassifyDic(self):
		try:
			dic = None
			for c in cs:
				cpath = os.path.join(LSI_DIR,c)
				if dic == None:
					dic = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
				else:
					dic.merge_with(corpora.Dictionary.load(os.path.join(cpath,'gs.dic')))
			dic.save(os.path.join(CLS_DIR, 'cls.dic'))
			return 'success'
		except Exception, e:
			logger.error(e)
			return 'failed'

	def trainClassify(self, db=db_local, db_primary=db_primary):
		try:
			dictionary = corpora.Dictionary.load(os.path.join(CLS_DIR, 'cls.dic'))
			t = datetime.datetime.now() - datetime.timedelta(days=180)
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
				return 'failed'
			dictionary = corpora.Dictionary.load(os.path.join(CLS_DIR, 'cls.dic'))
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
			pickle.dump(clf, open(os.path.join(CLS_DIR, 'cls.pkl'), 'wb'))
			return 'success'
		except Exception, e:
			logger.error(e)
			return 'failed'

	def classify(self, category, db=db_local, db_primary=db_primary):
		try:
			category = category.decode('utf-8') # chinese decode
			texts_origin = []
			ids = []
			for i in db.item.find({'category':category, 'category_origin':None}).limit(200):
				segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
				segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
				texts_origin.append(segs)
				ids.append(ObjectId(i['_id']))
			# logger.info('load classify data success')
			if len(texts_origin) == 0:
				logger.info('none data found')
				return 'failed'
			dictionary = corpora.Dictionary.load(os.path.join(CLS_DIR, 'cls.dic'))
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
			clf = pickle.load(open(os.path.join(CLS_DIR, 'cls.pkl'), 'rb'))
			pickle.dump(ids, open(os.path.join(CLS_DIR, 'test_ids.pkl'), 'wb'))
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
			db_primary.item.update({"_id":{"$in":unclears.keys()}}, {"$set":{'category_origin':category}}, multi=True)
			for nc in clears:
				db_primary.item.update({"_id":{"$in":clears[nc]}}, {"$set":{'category':cs[nc], 'category_origin':category}}, multi=True)
			veris = []
			for uci in db.item.find({"_id":{"$in":unclears.keys()}}):
				question = u'''请问下面的内容最可能属于哪一类？<br/>
							标题: {0}<br/>
							正文: {1}
						'''.format(uci['title'], uci['des'])
				option = [ o[0] for o in cs[unclears[uci['_id']]] ] + [u'其他']
				veris.append({ '_id':uci['_id'], 'rand':[random.random(), 0], \
					'question':question, 'option':option, 'data_origin':{'id':uci['_id'], 'prob':uci['_id']} })
			db_primary.verification.insert(veris, continue_on_error=True)
			return 'success'
		except:
			logger.info(e)
			return 'failed'

import win32serviceutil
import win32service
import win32event

class recserver(win32serviceutil.ServiceFramework):
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
	win32serviceutil.HandleCommandLine(recserver)
