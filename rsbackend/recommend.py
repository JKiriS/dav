#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from collections import defaultdict

stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
stopwords[' '] = 1
cs = json.load(file('cs.json'))
lsiindexdir = 'lsiindex'
		
def recommend1():
	items = []
	for i in db.item.find({},{'_id':1,'source':1,'category':1,'pubdate':1})\
			.sort('pubdate',pymongo.DESCENDING).limit(3000):
		items.append(i)

	lsi = models.LsiModel.load('gs.lsi')
	dic = corpora.Dictionary.load('gs.dic')
	index = similarities.MatrixSimilarity.load('gs.index')
	latesttime = items[0]['pubdate']
	for u in db.user.find(timeout=False):
		upre = db.upre.find_one({'_id':ObjectId(u['_id'])})
		oldrlist = db.rlist.find_one({'_id':ObjectId(u['_id'])})
		oldrlist = [] if oldrlist == None else oldrlist.get('rlist')
		
		vitemids = map(lambda a:a[0], upre['visited'][:150])
		if len(vitemids) == 0:
			continue
		visittime = {}
		for i in upre['visited'][:300]:
			visittime[i[0]] = i[1]
		latestvisit = max(visittime.values())
		texts_vitems = []
		for i in db.item.find({'_id':{'$in':vitemids}}):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
			deltaT = latestvisit - visittime.get(i['_id'])
			timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 15.))
			texts_vitems.append([segs, timefactor])
		simscore = None
		for i, tf in texts_vitems:
			test_bow = dic.doc2bow(i)
			test_lsi = lsi[test_bow]
			simscore = tf * index[test_lsi] if simscore == None else simscore + tf * index[test_lsi]
		simscore /= max(simscore)

		res = []
		for i in items:
			deltaT = latesttime - i['pubdate']
			timescore = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 1))
			sourcescore = math.sqrt(upre['source'].get(i['source'], .1))
			categoryscore = math.sqrt(upre['category'].get(i['category'], .1))
			res.append({'id':i['_id'], 'sourcescore':sourcescore, \
				'categoryscore':categoryscore, 'timescore':timescore})
		sourcemax = max(res, key=lambda a:a['sourcescore']).get('sourcescore', 1)
		categorymax = max(res, key=lambda a:a['categoryscore']).get('categoryscore', 1)
		for i in range(len(res)):
			randscore = 1 if random.random() > 0.3 else 0
			score = 0.1 * res[i].pop('sourcescore') / sourcemax + \
					0.2 * res[i].pop('categoryscore') / categorymax + \
					0.4 * simscore[i] + \
					0.2 * res[i].pop('timescore') + 0.1 * randscore
			# item which had been recommend lose score
			if res[i]['id'] in oldrlist: 
				score *= .9
			if res[i]['id'] in upre['visited']: 
				score *= 0
			res[i]['score'] = score
		res.sort(key=lambda a:a.pop('score'), reverse=True)
		res = map(lambda a: a['id'], res)
		db.rlist.save({'_id':ObjectId(u['_id']),'rlist':res})

def recommend(uid):
	upre = db.upre.find_one({'_id':ObjectId(uid)})
	oldrlist = db.rlist.find_one({'_id':ObjectId(uid)})
	oldrlist = [] if oldrlist == None else oldrlist.get('rlist')
	score = np.array([])
	ids = []
	for c in cs:
		score_c = None
		cpath = os.path.join(lsiindexdir, c)
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
		score = score / maxs
	score += np.random.random(len(score))
	res = [[ids[i], score[i]] for i in range(len(ids))]
	for r in res:
		if r[0] in oldrlist: 
			r[1] *= .9
		if r[0] in upre['visits']: 
			r[1] *= 0
	rlist = map(lambda y:y[0], sorted(res, key=lambda y:y[1], reverse=True)[:1000])
	db.rlist.save({'_id':ObjectId(uid),'rlist':rlist})

def run():
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	recommend()
	conn.close()

if __name__ == '__main__':
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	for u in db.user.find(timeout=False):
		recommend(u['_id'])
	conn.close()