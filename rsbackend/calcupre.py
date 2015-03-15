#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo
from bson import ObjectId
import datetime
import math
import jieba

stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') \
	for line in open('stopwords.txt') ])
stopwords[' '] = 1

def userPre(uid):
	pre = {'_id':ObjectId(uid),'source':{},'category':{},'wd':{},'visits':[]}
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
	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'search'})\
		.sort('timestamp', pymongo.DESCENDING).limit(500):
		# calculate timefactor 1 / (1 + exp( deltaT - 10))
		deltaT = latesttime - i['timestamp']
		timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 30.))
		if i['ttype'] == 'source':
			pre['source'][i['target']] = pre['source'].get(i['target'], 0) + 1 * timefactor
		elif i['ttype'] == 'category':
			pre['category'][i['target']] = pre['category'].get(i['target'], 0) + 1 * timefactor
		elif i['ttype'] == 'wd':
			segs = filter(lambda s:s not in stopwords, jieba.cut(i['target'], cut_all=False))
			for s in segs:
				pre['wd'][s] = pre['wd'].get(s, 0) + 1 * timefactor
	
	favos = {}
	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'addfavorite', 'ttype':'item'})\
			.sort('timestamp', pymongo.DESCENDING).limit(200):
		favos[ObjectId(i['target'])] = i['timestamp']
	visits = {}
	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'click', 'ttype':'item'})\
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
		userPre(u['_id'])
	conn.close()

