#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import os, sys, getopt

# opts, args = getopt.getopt(sys.argv[1:], "f:")
# # if len(opts) == 0:
# # 	exit()
# PARAMS_DIR = opts[0][1]
# sys.argv.remove(opts[0][0])
# sys.argv.remove(opts[0][1])
# if not os.path.isfile(PARAMS_DIR):
# 	PARAMS_DIR = "e:/dav/self.cfg"
PARAMS_DIR = "e:/dav/self.cfg"
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

cs = json.load(file(PARAMS['category']))
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
from gensim import corpora, models, similarities

class LsiFileManager:
	def __init__(self):
		self._lsis = {}
		self._dics = {}
		self._indexes = {}
		self._ids = {}
	def _wait(self, cpath):
		for i in range(10):
			if os.path.isfile(os.path.join(cpath, 'write.lock')):
				time.sleep(10)
			if i == 9:
				ex = FileError()
				ex.who = os.path.join(cpath, 'write.lock')
				raise ex
			else:
				break
	def _lock(self, cpath):
		if os.path.isfile(os.path.join(cpath, 'write.lock')):
			return False
		else:
			flock = open(os.path.join(cpath, 'write.lock'),'w+')
			flock.close()
			return True
	def _clearlock(self, cpath):
		if os.path.isfile(os.path.join(cpath, 'write.lock')):
			os.remove(os.path.join(cpath, 'write.lock'))
	def getlsi(self, category):
		if self._lsis.get(category, None) is None:
			cpath = os.path.join(LSI_DIR, category)
			self._wait(cpath)
			self._lsis[category] = models.LsiModel.load(os.path.join(cpath,'gs.lsi'))
		return self._lsis[category]
	def getdic(self, category):
		if self._dics.get(category, None) is None:
			cpath = os.path.join(LSI_DIR, category)
			self._wait(cpath)
			self._dics[category] = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
		return self._dics[category]
	def getindex(self, category):
		if self._indexes.get(category, None) is None:
			cpath = os.path.join(LSI_DIR, category)
			self._wait(cpath)
			self._indexes[category] = similarities.MatrixSimilarity.load(os.path.join(cpath,'gs.index'))
		return self._indexes[category]
	def getid(self, category):
		if self._ids.get(category, None) is None:
			cpath = os.path.join(LSI_DIR, category)
			self._wait(cpath)
			self._ids[category] = pickle.load(open(os.path.join(cpath,'ids.pkl'), 'rb'))
		return self._ids[category]
	def setlsi(self, category, newclsi):
		self._lsis[category] = newclsi
		cpath = os.path.join(LSI_DIR, category)
		self._wait(cpath)
		self._lock(cpath)
		self._lsis[category].save(os.path.join(cpath,'gs.lsi'))
		self._clearlock(cpath)
		return True
	def setdic(self, category, newcdic):
		self._dics[category] = newcdic
		cpath = os.path.join(LSI_DIR, category)
		self._wait(cpath)
		self._lock(cpath)
		self._dics[category].save(os.path.join(cpath,'gs.dic'))
		self._clearlock(cpath)	
		return True
	def setindex(self, category, newcindex):
		self._indexes[category] = newcindex
		cpath = os.path.join(LSI_DIR, category)
		self._wait(cpath)
		self._lock(cpath)
		self._indexes[category].save(os.path.join(cpath,'gs.index'))
		self._clearlock(cpath)
		return True
	def setid(self, category, newcid):
		self._ids[category] = newcid
		cpath = os.path.join(LSI_DIR, category)
		self._wait(cpath)
		self._lock(cpath)
		pickle.dump(self._ids[category], open(os.path.join(cpath,'ids.pkl'), 'wb'))
		self._clearlock(cpath)
		return True

lfm = LsiFileManager()

class RecHandler:
	def updateRList(self, uid):
		logger.info('update recommend list of user ' + uid)
		db = dbm.getlocal()
		upre = db.upre.find_one({'_id':ObjectId(uid)})
		if upre is None:
			ex = DataError()
			ex.who = 'upre(_id=' + uid + ')'
			raise ex
		oldrlist = db.rlist.find_one({'_id':ObjectId(uid)})
		oldrlist = [] if not oldrlist else oldrlist.get('rlist')
		score = np.array([])
		ids = []
		clicks = []
		favos = []
		for c in cs:
			score_c = None
			ids_c = lfm.getid(c)
			if len(ids_c) == 0:
				continue
			for i in db.item.find({'_id':{'$in':ids_c}},{'click_num':1,'favo_num':1}).sort('pubdate',pymongo.DESCENDING):
				clicks.append(i['click_num'])
				favos.append(i['favo_num'])
			ids += ids_c
			lsi = lfm.getlsi(c)
			dic = lfm.getdic(c)
			index = lfm.getindex(c)
			for i in db.item.find({'_id':{'$in':upre['visits']},'category':c}):
				segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
				segs *= 2
				segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
				test_bow = dic.doc2bow(segs)
				test_lsi = lsi[test_bow]
				score_c = index[test_lsi] if score_c is None else score_c + index[test_lsi]
			if score_c is not None:
				score = np.hstack(( score, score_c * math.sqrt(upre['category'].get(c, 1)) ))
			else :
				score = np.hstack(( score, np.zeros(len(ids_c)) ))
		if not len(ids) == len(score) == len(clicks) == len(favos):
			ex = DataError()
			ex.who = 'ids'
			raise ex 
		clicks = np.array(clicks)
		favos = np.array(favos)
		maxs = max(score)
		if maxs > 0:
			score = .3* score / maxs
		maxs = max(clicks)
		if maxs > 0:
			score += .2 * clicks / maxs
		maxs = max(favos)
		if maxs > 0:
			score += .3 * favos / maxs
		score += .2 * np.random.random(len(score))
		res = [[ids[i], score[i]] for i in range(len(ids))]
		for r in res:
			if r[0] in oldrlist: 
				r[1] *= .9
			if r[0] in upre['visits']: 
				r[1] *= 0
		rlist = map(lambda y:y[0], sorted(res, key=lambda y:y[1], reverse=True)[:1000])
		db_primary = dbm.getprimary()
		db_primary.rlist.save({'_id':ObjectId(uid),'rlist':rlist,'timestamp':now()})
		res = Result()
		res.success = True
		return res		

	def updateLsiIndex(self, category):
		category = category.decode('utf-8')
		logger.info('update lsi index of category ' + category)
		t = now() - datetime.timedelta(days=180)
		db = dbm.getlocal()
		itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
		texts_origin = []
		itemnum_c = db.item.find({'category':category,'pubdate':{'$gt':t}}).count()
		readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))
		cpath = os.path.join(LSI_DIR, category)
		itemIds = []
		for i in db.item.find({'category':category}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
			itemIds.append(i['_id'])
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		lfm.setid(category, itemIds)
		if len(texts_origin) == 0:
			ex = DataError()
			ex.who = 'texts_origin'
			raise ex
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		dictionary = lfm.getdic(category)
		if len(dictionary) == 0:
			ex = FileError()
			ex.who = 'lsidic'
			raise ex
		corpus = [dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus)
		corpus_tfidf = tfidf[corpus]
		lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=30)
		lfm.setlsi(category, lsi)
		lfm.setindex(category, similarities.MatrixSimilarity(lsi[corpus]))		
		res = Result()
		res.success = True
		return res

	def updateLsiDic(self, category):
		category = category.decode('utf-8')
		logger.info('update lsi dictionary of category ' + category)
		t = now() - datetime.timedelta(days=180)
		db = dbm.getlocal()
		itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()	
		itemnum_c = db.item.find({'category':category,'pubdate':{'$gt':t}}).count()
		readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))
		cpath = os.path.join(LSI_DIR, category)
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
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		lfm.setdic(category, corpora.Dictionary(texts))		
		res = Result()
		res.success = True
		return res

	def updateUPre(self, uid):
		logger.info('update preferences of user ' + uid)
		pre = {'_id':ObjectId(uid),'source':{},'category':{},'wd':{},'visits':[]}
		pre['timestamp'] = now()
		db = dbm.getlocal()
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
			res = Result()
			res.success = True
			res.msg = 'user' + uid + 'has no behavior history'
			return res
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
		db_primary = dbm.getprimary()
		db_primary.upre.save(pre)
		res = Result()
		res.success = True
		return res

import win32serviceutil
import win32service
import win32event

class recserver(win32serviceutil.ServiceFramework):
	_svc_name_ = "RecService"
	_svc_display_name_ = "recommend service"
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
		logger.info("run recommend service")
		handler = RecHandler()
		processor = Rec.Processor(handler)
		transport = TSocket.TServerSocket(PARAMS['recommend']['ip'], PARAMS['recommend']['port'])
		tfactory = TTransport.TBufferedTransportFactory()
		pfactory = TBinaryProtocol.TBinaryProtocolFactory()
		 
		server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
		 
		logger.info("Starting recommend service at port "+ repr(PARAMS['recommend']['port']) + " ...")
		server.serve()
		win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__=='__main__':
	win32serviceutil.HandleCommandLine(recserver)
		