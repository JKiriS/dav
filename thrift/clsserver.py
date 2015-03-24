#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
sys.path.append('./gen-py')
 
from cls import Cls
from cls.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

import pymongo
from bson import ObjectId
import datetime
import math
import random
import jieba
import pickle
import json
import os
import numpy as np
from gensim import corpora, models, similarities

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

import logging
import logging.config
logging.config.fileConfig("logger.conf")
logger = logging.getLogger("thrift")

PARAMS = json.load(file(os.path.join(BASE_DIR, 'self.cfg')))
PARAMS['db_ip'] = 'localhost'
stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') \
	for line in open(os.path.join(BASE_DIR, 'rsbackend/stopwords.txt')) ])
stopwords[' '] = 1
stopwords['.'] = 1
cs = json.load(file(os.path.join(BASE_DIR, 'rsbackend/cs.json')))
CLS_DIR = os.path.join(BASE_DIR, 'rsbackend/cls')

class DateEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.__str__()
		return json.JSONEncoder.default(self, obj)

conn = pymongo.Connection(PARAMS['db_ip'])
db = conn['feed']
db.authenticate(PARAMS['db_username'], PARAMS['db_password'])

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

	def trainClassify(self, db=db):
		try:
			# conn = pymongo.Connection(PARAMS['db_ip'])
			# db = conn['feed']
			# db.authenticate(PARAMS['db_username'], PARAMS['db_password'])
			dictionary = corpora.Dictionary.load(os.path.join(CLS_DIR, 'cls.dic'))
			t = datetime.datetime.now() - datetime.timedelta(days=60)
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

	def classify(self, category, db=db):
		try:
			category = category.decode('utf-8') # chinese decode
			# conn = pymongo.Connection(PARAMS['db_ip'])
			# db = conn['feed']
			# db.authenticate(PARAMS['db_username'], PARAMS['db_password'])
			texts_origin = []
			ids = []
			for i in db.item.find({'category':category}).limit(200):
				segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
				segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
				texts_origin.append(segs)
				ids.append(ObjectId(i['_id']))
			if len(texts_origin) == 0:
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
			# pickle.dump(ids, open(os.path.join(CLS_DIR, 'ids.pkl'), 'wb'))
			# pickle.dump(test_data, open(os.path.join(CLS_DIR, 'test.pkl'), 'wb'))
			# ids = pickle.load(open(os.path.join(CLS_DIR, 'ids.pkl'), 'rb'))
			# test_data = pickle.load(open(os.path.join(CLS_DIR, 'test.pkl'), 'rb'))
			clf = pickle.load(open(os.path.join(CLS_DIR, 'cls.pkl'), 'rb'))
			for i, d in enumerate(clf.predict_proba(test_data)):
				res = sorted(map(lambda a:(cs[a[0]], a[1]), enumerate(d)), \
					key=lambda a:a[1], reverse=True)
				if res[0][1] - res[1][1] < 0.2:
					top_prob = res[:3]
					random.shuffle(top_prob)
					si = db.item.find_one({'_id':ids[i]})
					if si != None:
						question = u'''请问下面的内容最可能属于哪一类？<br/>
							标题: {0}<br/>
							正文: {1}
						'''.format(si['title'], si['des'])
						option = [o[0] for o in top_prob] + [u'其他']
						db.verification.insert({ '_id':ObjectId(si['_id']), 'rand':[random.random(), 0], \
							'question':question, 'option':option, 'data_origin':{'id':si['_id'], 'prob':top_prob} })
				else:
					pass
				return 'success'
		except Exception, e:
			logger.error(e)
			return 'failed'

if __name__ == '__main__':
	handler = ClsHandler()
	processor = Cls.Processor(handler)
	transport = TSocket.TServerSocket("115.156.196.215", 9091)
	tfactory = TTransport.TBufferedTransportFactory()
	pfactory = TBinaryProtocol.TBinaryProtocolFactory()
	 
	# server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
	server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
	 
	print "Starting thrift server in python..."
	server.serve()
	print "done!"