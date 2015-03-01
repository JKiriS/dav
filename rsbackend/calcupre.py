#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo
from bson import ObjectId
import datetime
import math
import random
import jieba
from gensim import corpora, models, similarities
from collections import defaultdict

stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
stopwords[' '] = 1

def userPre(uid):
	pre = {'_id':ObjectId(uid),'source':{},'category':{},'wd':{},'visited':[],'favorite':[],'count':1}
	pre['timestamp'] = datetime.datetime.now()
	# get the latesttime 
	latest = db.behavior.find({'uid':ObjectId(uid)})\
		.sort('timestamp', pymongo.DESCENDING).limit(1)
	if latest.count() > 0:
		latesttime = latest[0]['timestamp']
	else :
		db.upre.save(pre)
		return pre
	# deal with search behavior
	behaviorlist = db.behavior.find({'uid':ObjectId(uid), 'action':'search'})\
		.sort('timestamp', pymongo.DESCENDING).limit(1000)
	for i in behaviorlist:
		# calculate timefactor 1 / (1 + exp( deltaT - 10))
		deltaT = latesttime - i['timestamp']
		timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
		if i['ttype'] == 'source':
			pre['source'][i['target']] = pre['source'].get(i['target'], 0) + 1 * timefactor
		elif i['ttype'] == 'category':
			pre['category'][i['target']] = pre['category'].get(i['target'], 0) + 1 * timefactor
		elif i['ttype'] == 'wd':
			pre['wd'][i['target']] = pre['wd'].get(i['target'], 0) + 1 * timefactor
	
	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'addfavorite', 'ttype':'item'})\
			.sort('timestamp', pymongo.DESCENDING).limit(200):
		pre['favorite'].append([ObjectId(i['target']), i['timestamp']])
	
	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'click', 'ttype':'item'})\
			.sort('timestamp', pymongo.DESCENDING).limit(300):
		pre['visited'].append([ObjectId(i['target']), i['timestamp']])

	items = {}
	for i, t in pre['visited']:
		items[i] = t
	latest = max(items.values())
	for i in db.item.find({'_id':{'$in':items.keys()}}):
		deltaT = latest - items[i['_id']]
		timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
		pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.2 * timefactor
		pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.2 * timefactor

	items = {}
	for i, t in pre['favorite']:
		items[i] = t
	latest = max(items.values())
	for i in db.item.find({'_id':{'$in':items.keys()}}):
		deltaT = latest - items[i['_id']]
		timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
		pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.5 * timefactor
		pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.5 * timefactor
	
	db.upre.save(pre)
	return pre
		
def run():
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	for u in db.user.find(timeout=False):
		userPre(u['_id'])
	conn.close()


if __name__ == '__main__':
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	for u in db.user.find(timeout=False):
		print u['_id']
		userPre(u['_id'])
	conn.close()

