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
import pickle
from gensim import corpora, models, similarities
from collections import defaultdict

stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
stopwords[' '] = 1
cs = json.load(file('cs.json'))
lsiindexdir = 'lsiindex'

now = lambda : datetime.datetime.now()
		
def update():
	t = datetime.datetime.now() - datetime.timedelta(days=180)
	itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
	for c in cs:
		texts_origin = []
		itemnum_c = db.item.find({'category':c,'pubdate':{'$gt':t}}).count()
		readnum = int(1000 * math.sqrt(itemnum_c / float(itemnum_all)))
		cpath = os.path.join(lsiindexdir,c)
		itemIds = []
		for i in db.item.find({'category':c}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
			itemIds.append(ObjectId(i['_id']))
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		pickle.dump(itemIds, open(os.path.join(cpath,'ids.pkl'), 'wb'))
		if len(texts_origin) == 0:
			continue
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		dictionary = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
		if len(dictionary) == 0:
			continue
		corpus = [dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus)
		corpus_tfidf = tfidf[corpus]
		lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=30)
		lsi.save(os.path.join(cpath,'gs.lsi'))
		index = similarities.MatrixSimilarity(lsi[corpus])
		index.save(os.path.join(cpath,'gs.index'))

def run():
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	update()
	db.job.insert({'module':'recommend', 'starttime':now() + datetime.timedelta(minutes=10)})
	conn.close()


if __name__ == '__main__':
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	update()
	conn.close()

