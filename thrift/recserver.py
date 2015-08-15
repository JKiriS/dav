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
			self._conn_local = pymongo.MongoClient(PARAMS['db_local']['ip'])
			self._db_local = self._conn_local['feed']
			self._db_local.authenticate(PARAMS['db_local']['username'], PARAMS['db_local']['password'])
			logger.info('local mongodb connection success')
		return self._db_local

	def getprimary(self):
		if self._db_primary is None:
			self._conn_primary = pymongo.MongoClient(PARAMS['db_primary']['ip'])
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

		self._model = None
		self._dic = None
		self._tfidf = None
		self._sim = None
		self._ids = None

		self.writeLock = Lock()

	def getmodel(self):
		if not self._model:
			with self.writeLock:
				try:
					self._model = models.LsiModel.load(os.path.join(self.LSI_DIR,'all.model'))
				except:
					pass
		return self._model

	def setmodel(self, newclsi):
		self._model = newclsi
		with self.writeLock:
			self._model.save(os.path.join(self.LSI_DIR,'all.model'))
		return True

	def getdic(self):
		if not self._dic:
			with self.writeLock:
				try:
					self._dic = corpora.Dictionary.load(os.path.join(self.LSI_DIR,'all.dic'))
				except:
					pass
		return self._dic

	def setdic(self, newcdic):
		self._dic = newcdic
		with self.writeLock:
			self._dic.save(os.path.join(self.LSI_DIR,'all.dic'))
		return True

	def getsim(self):
		if not self._sim:
			with self.writeLock:
				try:
					self._sim = similarities.Similarity.load(os.path.join(self.LSI_DIR,'all.sim'))
				except:
					pass
		return self._sim

	def setsim(self, newsim):
		self._sim = newsim
		with self.writeLock:
			self._sim.save(os.path.join(self.LSI_DIR,'all.sim'))
		return True

	def gettfidf(self):
		if not self._tfidf:
			with self.writeLock:
				try:
					self._tfidf = models.TfidfModel.load(os.path.join(self.LSI_DIR,'all.tfidf'))
				except:
					pass
		return self._tfidf

	def settfidf(self, newtfidf):
		self._tfidf = newtfidf
		with self.writeLock:
			self._tfidf.save(os.path.join(self.LSI_DIR,'all.tfidf'))
		return True

	def getids(self):
		if not self._ids:
			with self.writeLock:
				try:
					self._ids = pickle.load(open(os.path.join(self.LSI_DIR,'all.ids'), 'rb'))
				except:
					pass
		return self._ids

	def setids(self, newid):
		self._ids = newid
		with self.writeLock:
			pickle.dump(self._ids, open(os.path.join(self.LSI_DIR,'all.ids'), 'wb'))
		return True

lfm = LsiFileManager(LSI_DIR)

class RecHandler:

	def updateRList(self, uid):
		db = dbm.getprimary()
		upre = db.upre.find_one({'_id':ObjectId(uid)})
		model = lfm.getmodel()
		dic = lfm.getdic()
		sim = lfm.getsim()
		itemIds = lfm.getids()

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
			text_bow = dic.doc2bow(segs)
			text_sim = model[text_bow]
			data.append(map(lambda a:a[1], text_sim))
		if not visits_ids:
			return Result(success=True)
			
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
			center = list(enumerate(np.mean(data[label==i], axis=0)))
			center_score = sim[center]  * label_count.get(i) / len(label)
			# score = center_score if score is None else score + center_score
			score = center_score if score is None else np.vstack((score, center_score))

		score = np.amax(score, axis=0)

		latestitemIds, latestitemScores = itemIds[-1000:], score[-1000:]

		# latestitemScores += .2 * np.max(score) * np.random.random(len(latestitemScores))

		res = map(list, zip(latestitemIds, latestitemScores))
		for r in res:
			if r[0] in oldrlist: 
				r[1] *= .8
			if r[0] in visits: 
				r[1] = 0
		rlist = map(lambda y:y[0], sorted(res, key=lambda y:y[1], reverse=True))

		db.rlist.save({'_id':ObjectId(uid),'rlist':rlist,'timestamp':now()})

		return Result(success=True)

	def updateDic(self, batch_size=3000, skip=0):
		db = dbm.getlocal()
		dictionary = lfm.getdic()

		texts_origin = []
		for i in db.item.find().skip(skip).limit(batch_size):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		if not texts_origin:
			return Result(success=True)

		# generate and save(set) new dictionary
		if dictionary:
			dictionary.add_documents(texts_origin)
		else:
			dictionary = corpora.Dictionary(texts_origin)

		lfm.setdic(dictionary)

		return Result(success=True)

	def updateTfIdf(self, batch_size=3000):
		db = dbm.getlocal()
		dictionary = lfm.getdic()

		if not dictionary:
			raise FileError(who='dictionary')

		texts_origin = []
		for i in db.item.find().sort('pubdate', pymongo.DESCENDING).limit(batch_size):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		if len(texts_origin) == 0:
			return Result(success=True)

		corpus = [dictionary.doc2bow(text) for text in texts_origin]
		tfidf = models.TfidfModel(corpus)

		lfm.settfidf(tfidf)

		return Result(success=True)

	def updateModel(self, batch_size=2000, num_topics=100):
		db = dbm.getlocal()

		# load dictionary
		dictionary = lfm.getdic()
		if not dictionary:
			raise FileError(who='dictionary')
		tfidf = lfm.gettfidf()
		if not tfidf:
			raise FileError(who='tfidf')

		# collect text and cordnate item id(used for recommend)
		texts_origin = []
		itemIds = None
		APPENDMODE = False
		try:
			itemIds = lfm.getids()
		except Exception, e:
			pass
		if itemIds:
			items = db.item.find({'_id':{'$gt':itemIds[-1]}}).limit(batch_size)
			APPENDMODE = True
		else:
			items = db.item.find().limit(batch_size)
			itemIds = []
		for i in items:
			itemIds.append(i['_id'])
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		if len(texts_origin) == 0:
			raise DataError(who='texts_origin')

		# calculate text tfidf
		corpus = [dictionary.doc2bow(text) for text in texts_origin]
		corpus_tfidf = tfidf[corpus]

		#train lsi model and save lsi and index data
		if not APPENDMODE:
			model = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=num_topics)
			sim = similarities.Similarity(os.path.join(lfm.LSI_DIR, 'tmp/'), model[corpus], num_features=num_topics)
		else:
			model = lfm.getmodel()
			model.add_documents(corpus_tfidf)
			sim = lfm.getsim()
			sim.add_documents(model[corpus])
		lfm.setmodel(model)
		lfm.setsim(sim)
		lfm.setids(itemIds)	

		return Result(success=True)

	def lsiSearch(self, query, start=0, length=15):
		if not isinstance(query, unicode):
			query = query.decode('utf-8')

		model = lfm.getmodel()
		dictionary = lfm.getdic()
		sim = lfm.getsim()
		itemIds = lfm.getids()
		if not model:
			raise FileError(who='model')
		if not dictionary:
			raise FileError(who='dictionary')
		if not sim:
			raise FileError(who='sim')
		if not itemIds:
			raise FileError(who='itemIds')

		if len(itemIds) < start:
			raise DataError(who='start')
				
		segs = filter(lambda s:s not in stopwords, jieba.cut(query, cut_all=False))
		query_bow = dictionary.doc2bow(segs)
		query_lsi = model[query_bow]
		score = sim[query_lsi]
		
		searchresult =  sorted(zip(itemIds, score), key=lambda a:a[1], reverse=True)[start:start+length]
		res = Result(success=True, data={})
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

		return Result(success=True)

def test():
	handler = RecHandler()
	# handler.updateDic(skip=3000*33)
	# handler.updateTfIdf()
	# handler.updateModel(batch_size=1000)
	# print handler.lsiSearch('机器学习')
	# handler.updateUPre('5459d5ee7c46d50ae022b901')
	# print handler.updateRList('5459d5ee7c46d50ae022b901')

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