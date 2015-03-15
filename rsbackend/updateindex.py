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
from gensim import corpora, models, similarities
from collections import defaultdict

stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
stopwords[' '] = 1
cs = json.load(file('cs.json'))
lsiindexdir = 'lsiindex'

now = lambda : datetime.datetime.now()
		
def update():
	texts_origin = []
	t = datetime.datetime.now() - datetime.timedelta(days=60)
	itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
	for c in cs:
		itemnum_c = db.item.find({'category':c,'pubdate':{'$gt':t}}).count()
		readnum = round(1000*math.sqrt(itemnum_c/itemnum_all))
		cpath = os.path.join(lsiindexdir,c)
		for i in db.item.find({'category':c}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs *= 2
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		all_tokens = sum(texts_origin, [])
		token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		texts = [[word for word in text if word not in token_once] for text in texts_origin]
		dictionary = corpora.Dictionary(texts)
		dictionary.save(os.path.join(cpath,'gs.dic'))
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

