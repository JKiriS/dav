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

params = json.load(file('../self.cfg'))
stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
stopwords[' '] = 1
cs = json.load(file('cs.json'))
lsiindexdir = 'lsiindex'
clsdir = 'cls'

now = lambda : datetime.datetime.now()
		
def initDic():
	dic = None
	for c in cs:
		cpath = os.path.join(lsiindexdir,c)
		if dic == None:
			dic = corpora.Dictionary.load(os.path.join(cpath,'gs.dic'))
		else:
			dic.merge_with(corpora.Dictionary.load(os.path.join(cpath,'gs.dic')))
	dic.save(os.path.join(clsdir, 'cls.dic'))

def train():
	dictionary = corpora.Dictionary.load(os.path.join(clsdir, 'cls.dic'))
	t = datetime.datetime.now() - datetime.timedelta(days=60)
	itemnum_all = db.item.find({'pubdate':{'$gt':t}}).count()
		
	texts_origin = []
	train_target = np.array([])
	for ix, c in enumerate(cs):
		itemnum_c = db.item.find({'category':c,'pubdate':{'$gt':t}}).count()
		readnum = int(500 * math.sqrt(itemnum_c / float(itemnum_all)))
		tnum_before = len(texts_origin)
		for i in db.item.find({'category':c}).sort('pubdate',pymongo.DESCENDING).limit(readnum):
			segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
			segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
			texts_origin.append(segs)
		train_target = np.hstack(( train_target, np.zeros(len(texts_origin) - tnum_before) + ix ))
	if len(texts_origin) == 0:
		return
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
	pickle.dump(train_data, open(os.path.join(clsdir, 'data.pkl'), 'wb'))
	pickle.dump(train_target, open(os.path.join(clsdir, 'label.pkl'), 'wb'))
	from sklearn.naive_bayes import MultinomialNB  
	clf = MultinomialNB(alpha = 0.01)   
	clf.fit(train_data, train_target)
	pickle.dump(clf, open(os.path.join(clsdir, 'cls.pkl'), 'wb')) 

def classify():
	texts_origin = []
	ids = []
	for i in db.item.find({'category':u'综合'}).limit(200):
		segs = filter(lambda s:s not in stopwords, jieba.cut(i.pop('title'), cut_all=False))
		segs += filter(lambda s:s not in stopwords, jieba.cut(i.pop('des'), cut_all=False))
		texts_origin.append(segs)
		ids.append(ObjectId(i['_id']))
	if len(texts_origin) == 0:
		return
	dictionary = corpora.Dictionary.load(os.path.join(clsdir, 'cls.dic'))
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
	pickle.dump(ids, open(os.path.join(clsdir, 'ids.pkl'), 'wb'))
	pickle.dump(test_data, open(os.path.join(clsdir, 'test.pkl'), 'wb'))
	clf = pickle.load(open(os.path.join(clsdir, 'cls.pkl'), 'rb'))
	pred = clf.predict(test_data) 
	pickle.dump(pred, open(os.path.join(clsdir, 'res.pkl'), 'wb'))
	return pred

def run():
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate(params['db_username'], params['db_password'])
	db.job.insert({'module':'recommend', 'starttime':now() + datetime.timedelta(minutes=10)})
	conn.close()

def test():
	# train_data = pickle.load(open(os.path.join(clsdir, 'data.pkl'), 'rb'))
	# train_target = pickle.load(open(os.path.join(clsdir, 'label.pkl'), 'rb'))
	# from sklearn.svm import SVC    
	# svclf = SVC(kernel = 'linear')  
	# svclf.fit(train_data, train_target) 
	# from sklearn.naive_bayes import MultinomialNB  
	# clf = MultinomialNB(alpha = 0.01)   
	# clf.fit(train_data, train_target)
	# pickle.dump(clf, open(os.path.join(clsdir, 'cls.pkl'), 'wb')) 
	ids = pickle.load(open(os.path.join(clsdir, 'ids.pkl'), 'rb'))
	test_data = pickle.load(open(os.path.join(clsdir, 'test.pkl'), 'rb'))
	svclf = pickle.load(open(os.path.join(clsdir, 'cls.pkl'), 'rb'))
	# print svclf.class_count_
	for i, d in enumerate(svclf.predict_proba(test_data)) :
		res = sorted(map(lambda a:(cs[a[0]], a[1]), enumerate(d)), \
			key=lambda a:a[1], reverse=True)
		if res[0][1] - res[1][1] < 0.2:
			top_prob = res[:3]
			random.shuffle(top_prob)
			si = db.item.find_one({'_id':ids[i]})
			if si != None:
				question = u'''请问下面的内容最可能属于哪一类？<br/>
					标题: {0}<br/>
					正文: {1}
				'''.format(si['title'], si['des'])
				option = [o[0] for o in top_prob] + [u'其他']
				db.verification.insert({ 'question':question, 'option':option, 'rand':[random.random(), 0], \
					'data_origin':{'id':si['_id'], 'prob':top_prob} })
		else:
			pass

'''
0:科技 1:娱乐 2:体育 3:文化 4:军事 5:财经 6:时政
'''

if __name__ == '__main__':
	global db
	conn = pymongo.Connection(params['db_ip'])
	db = conn['feed']
	db.authenticate(params['db_username'], params['db_password'])
	test()
	conn.close()

