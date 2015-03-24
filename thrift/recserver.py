#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
sys.path.append('./gen-py')
 
from rec import Rec
from rec.ttypes import *

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
LSI_DIR = os.path.join(BASE_DIR, 'rsbackend/lsiindex')

class DateEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.__str__()
		return json.JSONEncoder.default(self, obj)

conn = pymongo.Connection(PARAMS['db_ip'])
db = conn['feed']
db.authenticate(PARAMS['db_username'], PARAMS['db_password'])

class RecHandler:
	def updateRList(self, uid, db=db):
		try:
			# conn = pymongo.Connection(PARAMS['db_ip'])
			# db = conn['feed']
			# db.authenticate(PARAMS['db_username'], PARAMS['db_password'])
			upre = db.upre.find_one({'_id':ObjectId(uid)})
			oldrlist = db.rlist.find_one({'_id':ObjectId(uid)})
			oldrlist = [] if oldrlist == None else oldrlist.get('rlist')
			score = np.array([])
			ids = []
			for c in cs:
				score_c = None
				cpath = os.path.join(LSI_DIR, c)
				itemIds = pickle.load(open(os.path.join(cpath,'ids.pkl'), 'rb'))
				if len(itemIds) == 0:
					continue
				ids += itemIds
				lsi = models.LsiModel.load(os.path.join(cpath,'gs.lsi'))
				dic = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
				index = similarities.MatrixSimilarity.load(os.path.join(cpath,'gs.index'))
				for i in db.item.find({'_id':{'$in':upre['visits']},'category':c}):
					segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
					segs *= 2
					segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
					test_bow = dic.doc2bow(segs)
					test_lsi = lsi[test_bow]
					score_c = index[test_lsi] if score_c == None else score_c + index[test_lsi]
				if score_c != None:
					score = np.hstack(( score, score_c * math.sqrt(upre['category'].get(c, 1)) ))
				else :
					score = np.hstack(( score, np.zeros(len(itemIds)) ))
			maxs = max(score)
			if maxs > 0:
				score = .7 * score / maxs
			score += .3 * np.random.random(len(score))
			res = [[ids[i], score[i]] for i in range(len(ids))]
			for r in res:
				if r[0] in oldrlist: 
					r[1] *= .9
				if r[0] in upre['visits']: 
					r[1] *= 0
			rlist = map(lambda y:y[0], sorted(res, key=lambda y:y[1], reverse=True)[:1000])
			db.rlist.save({'_id':ObjectId(uid),'rlist':rlist,'timestamp':datetime.datetime.now()})
			return 'success'
		except Exception, e:
			logger.error(e)
			return 'failed'

	def updateLsiIndex(self, category, db=db):
		try:
			category = category.decode('utf-8')
			# conn = pymongo.Connection(PARAMS['db_ip'])
			# db = conn['feed']
			# db.authenticate(PARAMS['db_username'], PARAMS['db_password'])
			t = datetime.datetime.now() - datetime.timedelta(days=180)
			itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
			texts_origin = []
			itemnum_c = db.item.find({'category':category,'pubdate':{'$gt':t}}).count()
			readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))
			cpath = os.path.join(LSI_DIR, category)
			itemIds = []
			for i in db.item.find({'category':category}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
				itemIds.append(ObjectId(i['_id']))
				segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
				segs *= 2
				segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
				texts_origin.append(segs)
			pickle.dump(itemIds, open(os.path.join(cpath,'ids.pkl'), 'wb'))
			if len(texts_origin) == 0:
				return 'success'
			all_tokens = sum(texts_origin, [])
			token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
			texts = [[word for word in text if word not in token_once] for text in texts_origin]
			dictionary = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
			if len(dictionary) == 0:
				return 'dict error'
			corpus = [dictionary.doc2bow(text) for text in texts]
			tfidf = models.TfidfModel(corpus)
			corpus_tfidf = tfidf[corpus]
			lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=30)
			lsi.save(os.path.join(cpath,'gs.lsi'))
			index = similarities.MatrixSimilarity(lsi[corpus])
			index.save(os.path.join(cpath,'gs.index'))
			return 'success'
		except Exception, e:
			logger.error(e)
			return 'failed'

	def updateLsiDic(self, category, db=db):
		try:
			category = category.decode('utf-8')
			# conn = pymongo.Connection(PARAMS['db_ip'])
			# db = conn['feed']
			# db.authenticate(PARAMS['db_username'], PARAMS['db_password'])
			t = datetime.datetime.now() - datetime.timedelta(days=180)
			itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
			texts_origin = []
			itemnum_c = db.item.find({'category':category,'pubdate':{'$gt':t}}).count()
			readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))
			cpath = os.path.join(LSI_DIR, category)
			for i in db.item.find({'category':category}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
				segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
				segs *= 2
				segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
				texts_origin.append(segs)
			all_tokens = sum(texts_origin, [])
			token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
			texts = [[word for word in text if word not in token_once] for text in texts_origin]
			dictionary = corpora.Dictionary(texts)
			dictionary.save(os.path.join(cpath,'gs.dic'))
			return 'success'
		except Exception, e:
			logger.error(e)
			return 'failed'

	def updateUPre(self, uid, db=db):
		try:
			# conn = pymongo.Connection(PARAMS['db_ip'])
			# db = conn['feed']
			# db.authenticate(PARAMS['db_username'], PARAMS['db_password'])
			pre = {'_id':ObjectId(uid),'source':{},'category':{},'wd':{},'visits':[]}
			pre['timestamp'] = datetime.datetime.now()
			for s in db.source.find():
				pre['source'][s['name']] = 0
			for c in db.category.find():
				pre['category'][c['name']] = 0
			# get the latesttime 
			latest = db.behavior.find({'uid':ObjectId(uid)})\
				.sort('timestamp', pymongo.DESCENDING).limit(1)
			if latest.count() > 0:
				latesttime = latest[0]['timestamp']
			else :
				db.upre.save(pre)
				return 'success'
			# search
			for i in db.behavior.find({'uid':ObjectId(uid), 'action':'search'})\
				.sort('timestamp', pymongo.DESCENDING).limit(500):
				deltaT = latesttime - i['timestamp']
				timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
				segs = filter(lambda s:s not in stopwords, jieba.cut(i['target'], cut_all=False))
				for s in segs:
					pre['wd'][s] = pre['wd'].get(s, 0) + 1 * timefactor
			# visit source
			for i in db.behavior.find({'uid':ObjectId(uid), 'action':'visitsource'})\
				.sort('timestamp', pymongo.DESCENDING).limit(500):
				deltaT = latesttime - i['timestamp']
				timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
				pre['source'][i['target']] = pre['source'].get(i['target'], 0) + 1.2 * timefactor
			# visit category
			for i in db.behavior.find({'uid':ObjectId(uid), 'action':'visitcategory'})\
				.sort('timestamp', pymongo.DESCENDING).limit(500):
				deltaT = latesttime - i['timestamp']
				timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
				pre['category'][i['target']] = pre['category'].get(i['target'], 0) + 1.2 * timefactor
			#clickitem
			visits = {}
			for i in db.behavior.find({'uid':ObjectId(uid), 'action':'clickitem'})\
					.sort('timestamp', pymongo.DESCENDING).limit(300):
				visits[ObjectId(i['target'])] = i['timestamp']
			if len(visits) > 0:
				latest = max(visits.values())
				for i in db.item.find({'_id':{'$in':visits.keys()}}):
					deltaT = latest - visits[i['_id']]
					timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
					pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.2 * timefactor
					pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.2 * timefactor
					segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
					for s in segs:
						pre['wd'][s] = pre['wd'].get(s, 0) + 1 * timefactor
			#favo item
			favos = {}
			for i in db.behavior.find({'uid':ObjectId(uid), 'action':'addfavorite'})\
					.sort('timestamp', pymongo.DESCENDING).limit(200):
				favos[ObjectId(i['target'])] = i['timestamp']
			if len(favos) > 0:
				latest = max(favos.values())
				for i in db.item.find({'_id':{'$in':favos.keys()}}):
					deltaT = latest - favos[i['_id']]
					timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
					pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.5 * timefactor
					pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.5 * timefactor
					segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
					for s in segs:
						pre['wd'][s] = pre['wd'].get(s, 0) + 1 * timefactor
			pre['wd'] = dict(sorted(pre['wd'].items(), key = lambda y:y[1], reverse=True)[:100])
			pre['visits'] = visits.keys()
			db.upre.save(pre)
			return 'success'
		except Exception, e:
			logger.error(e)
			return 'failed'

if __name__ == '__main__':
	handler = RecHandler()
	processor = Rec.Processor(handler)
	transport = TSocket.TServerSocket("115.156.196.215", 9090)
	tfactory = TTransport.TBufferedTransportFactory()
	pfactory = TBinaryProtocol.TBinaryProtocolFactory()
	 
	# server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
	server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
	 
	print "Starting thrift server in python..."
	server.serve()
	print "done!"