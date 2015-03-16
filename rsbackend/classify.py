#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo
from bson import ObjectId
import datetime
import math
import random
import os
import jieba
import json
import numpy as np
import pickle
from gensim import corpora, models

stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
stopwords[' '] = 1
cs = json.load(file('cs.json'))
lsiindexdir = 'lsiindex'
clsdir = 'cls'

now = lambda : datetime.datetime.now()
		
def initDic():
	for c in cs:
		cpath = os.path.join(lsiindexdir,c)
		if dic == None:
			dic = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
		else:
			dic.merge_with(corpora.Dictionary.load(os.path.join(cpath,'gs.dic')))
	dic.save(os.path.join(clsdir, 'cls.dic'))

def train():
	dictionary = corpora.Dictionary.load('gs.dic')
	t = datetime.datetime.now() - datetime.timedelta(days=60)
	itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
		
	texts_origin = []
	train_target = np.array([])
	for ix, c in enumerate(cs):
		itemnum_c = db.item.find({'category':c,'pubdate':{'$gt':t}}).count()
		readnum = int(200 * math.sqrt(itemnum_c / float(itemnum_all)))
		tnum_before = len(texts_origin)
		for i in db.item.find({'category':c}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		train_target = np.hstack(( train_target, np.zeros(len(texts_origin) - tnum_before) + ix ))
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
	from sklearn.svm import SVC    
	svclf = SVC(kernel = 'linear')  
	svclf.fit(train_data, train_target) 
	pickle.dumps(svclf, open(os.path.join(clsdir, 'cls.pkl'), 'wb')) 

def classify():
	texts_origin = []
	ids = []
	for i in db.item.find({'category':u'综合'}):
		segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
		segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
		texts_origin.append(segs)
		ids.append(ObjectId(i['_id']))
	if len(texts_origin) == 0:
		return
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
	svclf = pickle.loads(open(os.path.join(clsdir, 'cls.pkl'), 'rb'))
	pred = svclf.predict(test_data) 
	return pred

def run():
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	db.job.insert({'module':'recommend', 'starttime':now() + datetime.timedelta(minutes=10)})
	conn.close()


if __name__ == '__main__':
	global db
	conn = pymongo.Connection('54.187.240.68')
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	train()
	conn.close()

