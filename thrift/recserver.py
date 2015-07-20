#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import os, sys
import optparse

parser = optparse.OptionParser()
parser.add_option('-f', dest="PARAMS_DIR")
parser.set_defaults(PARAMS_DIR="/home/jkiris/dav/self.cfg")

opt, args = parser.parse_args()

PARAMS_DIR = opt.PARAMS_DIR
import json
PARAMS = json.load(file(PARAMS_DIR))
sys.path.append(PARAMS['thrift']['gen-py'])
 
from rec import Rec
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

cs = [c['name'] for c in dbm.getprimary().category.find()]

from bson import ObjectId
import datetime, time
import math
import random
import pickle
import numpy as np
from sklearn import cluster, preprocessing
from gensim import corpora, models, similarities

from threading import Lock

class LsiFileManager:

	def __init__(self, LSI_DIR):
		self.LSI_DIR = LSI_DIR

		self._lsis = {}
		self._dics = {}
		self._indexes = {}
		self._ids = {}

		self.writeLock = Lock()

	def getlsi(self, category):
		if not self._lsis.get(category):
			cpath = os.path.join(self.LSI_DIR, category)
			with self.writeLock:
				self._lsis[category] = models.LsiModel.load(os.path.join(cpath,'gs.lsi'))
		return self._lsis.get(category)

	def getdic(self, category):
		if not self._dics.get(category):
			cpath = os.path.join(self.LSI_DIR, category)
			with self.writeLock:
				self._dics[category] = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
		return self._dics.get(category)

	def getindex(self, category):
		if not self._indexes.get(category):
			cpath = os.path.join(self.LSI_DIR, category)
			with self.writeLock:
				self._indexes[category] = similarities.Similarity.load(os.path.join(cpath,'gs.index'))
		return self._indexes.get(category)

	def getid(self, category):
		if not self._ids.get(category):
			cpath = os.path.join(self.LSI_DIR, category)
			with self.writeLock:
				self._ids[category] = pickle.load(open(os.path.join(cpath,'ids.pkl'), 'rb'))
		return self._ids.get(category)

	def setlsi(self, category, newclsi):
		self._lsis[category] = newclsi
		cpath = os.path.join(self.LSI_DIR, category)
		if not os.path.exists(cpath):
			os.makedirs(cpath)
		with self.writeLock:
			self._lsis[category].save(os.path.join(cpath,'gs.lsi'))
		return True

	def setdic(self, category, newcdic):
		self._dics[category] = newcdic
		cpath = os.path.join(self.LSI_DIR, category)
		if not os.path.exists(cpath):
			os.makedirs(cpath)
		with self.writeLock:
			self._dics[category].save(os.path.join(cpath,'gs.dic'))
		return True

	def setindex(self, category, newcindex):
		self._indexes[category] = newcindex
		cpath = os.path.join(self.LSI_DIR, category)
		if not os.path.exists(cpath):
			os.makedirs(cpath)
		with self.writeLock:
			self._indexes[category].save(os.path.join(cpath,'gs.index'))
		return True

	def setid(self, category, newcid):
		self._ids[category] = newcid
		cpath = os.path.join(self.LSI_DIR, category)
		if not os.path.exists(cpath):
			os.makedirs(cpath)
		with self.writeLock:
			pickle.dump(self._ids[category], open(os.path.join(cpath,'ids.pkl'), 'wb'))
		return True

lfm = LsiFileManager(LSI_DIR)

class RecHandler:

	def updateRList(self, uid):
		db = dbm.getprimary()
		upre = db.upre.find_one({'_id':ObjectId(uid)})
		lsi = lfm.getlsi('search')
		dic = lfm.getdic('search')
		index = lfm.getindex('search')
		itemIds = lfm.getid('search')

		oldrlist = db.rlist.find_one({'_id':ObjectId(uid)})
		oldrlist = [] if not oldrlist else oldrlist.get('rlist')

		visits = {}
		for i in db.behavior.find({'uid':ObjectId(uid), 'action':'clickitem'})\
				.sort('timestamp', pymongo.DESCENDING).limit(1000):
			visits[ObjectId(i['target'])] = 1
		upre['visits'] = visits.keys()
		db.upre.save(upre)

		data = []
		visits_ids = []
		for i in db.item.find({'_id':{'$in':visits.keys()}}):
			visits_ids.append(i['_id'])
			segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
			test_bow = dic.doc2bow(segs)
			test_lsi = lsi[test_bow]
			data.append(map(lambda a:a[1], test_lsi))
		if not visits_ids:
			res = Result()
			res.success = True
			return res
			
		data = np.array(data)

		K = 5

		# data = preprocessing.scale(data)  #  Z-Score
		# data = preprocessing.MinMaxScaler().fit_transform(data)  #  range
		data = preprocessing.normalize(data, norm='l2')  #  l2 Normalization

		k_means = cluster.KMeans(K)
		k_means.fit(data)

		label = k_means.labels_

		label_count = {}
		for i in label:
			label_count[i] = label_count.get(i, 0) + 1

		max_label = sorted(label_count.items(), key=lambda a:a[1])[-1][0]

		score = None
		for i in range(K):
			if i != max_label:
				continue
			center = list(enumerate(np.mean(data[label==i], axis=0)))
			center_score = index[center]  * label_count.get(i) / len(label)
			score = center_score if score is None else score + center_score

		latestitemIds, latestitemScores = itemIds[-2000:], score[-2000:]

		latestitemScores += .2 * np.random.random(len(latestitemScores))

		res = map(list, zip(latestitemIds, latestitemScores))
		for r in res:
			if r[0] in oldrlist: 
				r[1] *= .8
			if r[0] in visits: 
				r[1] = 0
		rlist = map(lambda y:y[0], sorted(res, key=lambda y:y[1], reverse=True))

		db.rlist.save({'_id':ObjectId(uid),'rlist':rlist,'timestamp':now()})

		res = Result()
		res.success = True
		return res

	def updateLsiIndex(self, category):
		if not isinstance(category, unicode):
			category = category.decode('utf-8')
		logger.info('update lsi index of category ' + category)
		db = dbm.getlocal()

		# calculate read item num based on total ratio of the category
		t = now() - datetime.timedelta(days=180)		
		itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
		itemnum_c = db.item.find({'category':category,'pubdate':{'$gt':t}}).count()
		readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))

		# load dictionary
		dictionary = lfm.getdic(category)
		if not dictionary:
			self.updateLsiDic(category)
			dictionary = lfm.getdic(category)

		# collect text and cordnate item id(used for recommend)
		texts_origin = []
		itemIds = []
		for i in db.item.find({'category':category}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
			itemIds.append(i['_id'])
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		if len(texts_origin) == 0:
			ex = DataError()
			ex.who = 'texts_origin'
			raise ex

		# calculate text tfidf
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		corpus = [dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus)
		corpus_tfidf = tfidf[corpus]

		#train lsi model and save lsi and index data
		lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=30)
		lfm.setlsi(category, lsi)
		lfm.setindex(category, similarities.MatrixSimilarity(lsi[corpus]))	
		lfm.setid(category, itemIds)	
		res = Result()
		res.success = True
		return res

	def updateLsiDic(self, category):
		if not isinstance(category, unicode):
			category = category.decode('utf-8')
		logger.info('update lsi dictionary of category ' + category)
		db = dbm.getlocal()

		# calculate read item num based on total ratio of the category
		t = now() - datetime.timedelta(days=180)
		itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()	
		itemnum_c = db.item.find({'category':category,'pubdate':{'$gt':t}}).count()
		readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))

		# collect text data
		texts_origin = []
		for i in db.item.find({'category':category}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		if len(texts_origin) == 0:
			ex = DataError()
			ex.who = 'texts_origin'
			raise ex

		# generate and save(set) new dictionary 
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		lfm.setdic(category, corpora.Dictionary(texts))
		res = Result()
		res.success = True
		return res

	def updateLsiSearchDic(self):
		db = dbm.getlocal()

		texts_origin = []
		for i in db.item.find().limit(3000):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		if len(texts_origin) == 0:
			ex = DataError()
			ex.who = 'texts_origin'
			raise ex

		# generate and save(set) new dictionary 
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		lfm.setdic('search', corpora.Dictionary(texts))
		res = Result()
		res.success = True
		return res

	def updateLsiSearchIndex(self):
		db = dbm.getlocal()

		# load dictionary
		dictionary = lfm.getdic('search')
		if not dictionary:
			self.updateLsiDic('search')
			dictionary = lfm.getdic('search')

		# collect text and cordnate item id(used for recommend)
		texts_origin = []
		itemIds = []
		APPENDMODE = False
		try:
			itemIds = lfm.getid('search')
		except Exception, e:
			print e
		if itemIds:
			items = db.item.find({'_id':{'$gt':itemIds[-1]}}).limit(3000)
			APPENDMODE = True
		else:
			items = db.item.find().limit(3000)
		for i in items:
			itemIds.append(i['_id'])
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		if len(texts_origin) == 0:
			ex = DataError()
			ex.who = 'texts_origin'
			raise ex

		# calculate text tfidf
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		corpus = [dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus)
		corpus_tfidf = tfidf[corpus]

		#train lsi model and save lsi and index data
		if not APPENDMODE:
			lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=200)
			index = similarities.Similarity('/home/jkiris/dav/tmp/', lsi[corpus], num_features=200)
		else:
			lsi = lfm.getlsi('search')
			lsi.add_documents(corpus_tfidf)
			index = lfm.getindex('search')
			index.add_documents(lsi[corpus])
		lfm.setlsi('search', lsi)
		lfm.setindex('search', index)
		lfm.setid('search', itemIds)	
		res = Result()
		res.success = True
		return res

	def lsiSearch(self, query, start=0, length=15):
		if not isinstance(query, unicode):
			query = query.decode('utf-8')
		lsi = lfm.getlsi('search')
		dic = lfm.getdic('search')
		index = lfm.getindex('search')
		itemIds = lfm.getid('search')
		if len(itemIds) < start:
			ex = DataError()
			ex.who = 'start'
			raise ex
				
		segs = filter(lambda s:s not in stopwords, jieba.cut(query, cut_all=False))
		test_bow = dic.doc2bow(segs)
		test_lsi = lsi[test_bow]
		score = index[test_lsi]
		
		searchresult =  sorted(zip(itemIds, score), key=lambda a:a[1], reverse=True)[start:start+length]
		res = Result()
		res.success = True
		res.data = {}
		res.data["searchresult"] = str( map(lambda i:i[0], filter(lambda i: i[1]>=.05, searchresult)) )
		if searchresult[-1][1] < 0.05:
			res.data["hasmore"] = str(False)
		else:
			res.data["hasmore"] = str(True)
		return res

	def updateUPre(self, uid):
		logger.info('update preferences of user ' + uid)
		db = dbm.getlocal()
		now_time = now()

		# create and init user pre data
		pre = {'_id':ObjectId(uid),'source':{},'category':{},'wd':{},'visits':[],'timestamp':now_time}
		source_count = db.source.count()
		category_count = db.category.count()
		pre['source'] = dict.fromkeys([s['name'] for s in db.source.find()], 1 / source_count)
		pre['category'] = dict.fromkeys([c['name'] for c in db.category.find()], 1 / category_count)
		
		# collect search history
		for i in db.behavior.find({'uid':ObjectId(uid), 'action':'search'})\
				.sort('timestamp', pymongo.DESCENDING).limit(500):
			deltaT = now_time - i['timestamp']
			timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
			segs = filter(lambda s:s not in stopwords, jieba.cut(i['target'], cut_all=False))
			for s in segs:
				pre['wd'][s] = pre['wd'].get(s, 0) + 1 * timefactor

		# collect 500 latest source visit history
		for i in db.behavior.find({'uid':ObjectId(uid), 'action':'visitsource'})\
				.sort('timestamp', pymongo.DESCENDING).limit(500):
			deltaT = now_time - i['timestamp']
			timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
			pre['source'][i['target']] = pre['source'].get(i['target'], 0) + 1.2 * timefactor

		# collect 500 latest category visit history
		for i in db.behavior.find({'uid':ObjectId(uid), 'action':'visitcategory'})\
				.sort('timestamp', pymongo.DESCENDING).limit(500):
			deltaT = now_time - i['timestamp']
			timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
			pre['category'][i['target']] = pre['category'].get(i['target'], 0) + 1.2 * timefactor
		
		# collect item click history
		visits = {}
		for i in db.behavior.find({'uid':ObjectId(uid), 'action':'clickitem'})\
				.sort('timestamp', pymongo.DESCENDING).limit(300):
			visits[ObjectId(i['target'])] = i['timestamp']
		if len(visits) > 0:
			for i in db.item.find({'_id':{'$in':visits.keys()}}):
				deltaT = now_time - visits[i['_id']]
				timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
				pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.2 * timefactor
				pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.2 * timefactor
				segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
				for s in segs:
					pre['wd'][s] = pre['wd'].get(s, 0) + 1 * timefactor
		
		# collect favo item history
		favos = {}
		for i in db.behavior.find({'uid':ObjectId(uid), 'action':'addfavorite'})\
				.sort('timestamp', pymongo.DESCENDING).limit(200):
			favos[ObjectId(i['target'])] = i['timestamp']
		if len(favos) > 0:
			for i in db.item.find({'_id':{'$in':favos.keys()}}):
				deltaT = now_time - favos[i['_id']]
				timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
				pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.5 * timefactor
				pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.5 * timefactor
				segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
				for s in segs:
					pre['wd'][s] = pre['wd'].get(s, 0) + 1 * timefactor

		# data uniform and cut
		pre['wd'] = dict(sorted(pre['wd'].items(), key = lambda y:y[1], reverse=True)[:100])
		pre['visits'] = visits.keys()
		source_sum = sum(pre['source'].values())
		if source_sum <= 0: source_sum = 1
		for key in pre['source']:
			pre['source'][key] /= source_sum
		category_sum = sum(pre['category'].values())
		if category_sum <= 0: category_sum = 1
		for key in pre['category']:
			pre['category'][key] /= category_sum

		# save upre data to database
		db_primary = dbm.getprimary()
		db_primary.upre.save(pre)
		res = Result()
		res.success = True
		return res

def initRecommend():
	db = dbm.getprimary()
	handler = RecHandler()
	for c in db.category.find():
		handler.updateLsiDic(c['name'])
		handler.updateLsiIndex(c['name'])

def test():
	handler = RecHandler()
	# handler.updateUPre('5459d5ee7c46d50ae022b901')
	# handler.updateLsiDic('文化')
	# handler.updateLsiIndex(u'文化')
	# handler.updateRList('5459d5ee7c46d50ae022b901')
	# handler.updateLsiSearchDic()
	# handler.updateLsiSearchIndex()
	# print handler.lsiSearch('机器学习')

def main():
	logger.info("run recommend service")
	handler = RecHandler()
	processor = Rec.Processor(handler)
	transport = TSocket.TServerSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
	tfactory = TTransport.TBufferedTransportFactory()
	pfactory = TBinaryProtocol.TBinaryProtocolFactory()
	 
	server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
	 
	logger.info("Starting recommend service at port "+ repr(PARAMS['recommend']['port']) + " ...")
	server.serve()

if __name__=='__main__':
	main()
	
