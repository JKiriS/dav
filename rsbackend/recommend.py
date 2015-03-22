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

params = json.load(file('../self.cfg'))
stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
stopwords[' '] = 1
cs = json.load(file('cs.json'))
lsiindexdir = 'lsiindex'
		

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
		score = .7 * score / maxs
	score += .3 * np.random.random(len(score))
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
	db.authenticate(params['db_username'], params['db_password'])
	recommend()
	conn.close()

if __name__ == '__main__':
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate(params['db_username'], params['db_password'])
	for u in db.user.find(timeout=False):
		recommend(u['_id'])
	conn.close()