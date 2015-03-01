#!/usr/bin/env python
# -*- coding: utf-8 -*-

# db = mongoconn()

	# import jieba
	# from sklearn import feature_extraction
	# from sklearn.feature_extraction.text import TfidfTransformer
	# from sklearn.feature_extraction.text import CountVectorizer
	# from sklearn.decomposition import PCA
	# import numpy as np
	# stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('stopwords.txt') ])
	# f = open('res.txt', 'w+')
	# words = {}
	# for i in db.item.find({'_id':{'$in':pre.get('item',[])}}):
	# 	if not i.get('title'):
	# 		continue
	# 	segs = jieba.cut(i['title'], cut_all=False)
	# 	for seg in segs:
	# 		if seg not in stopwords and seg != ' ':
	# 			words[seg] = 1 if seg not in words else words[seg]+1

	# for i in sorted(words.iteritems(), key=lambda a:a[1], reverse=True):
	# 	f.write(i[0].encode('utf-8')+':'+repr(i[1])+'\n')
	# f.close()
	# docs = []
	# for i in db.item.find({'_id':{'$in':pre.get('item',[])}}):
	# 	if not i.get('title'):
	# 		continue
	# 	segs = jieba.cut(i['title'], cut_all=False)
	# 	words = []
	# 	for seg in segs:
	# 		if seg not in stopwords and seg != ' ':
	# 			words.append(seg)#words[seg] = 1 if seg not in words else words[seg]+1
	# 	docs.append(' '.join(words))
	# vectorizer = CountVectorizer()
	# transformer = TfidfTransformer()
	# tfidf = transformer.fit_transform(vectorizer.fit_transform(docs))
	# word = vectorizer.get_feature_names()  #所有文本的关键字
	# weight = tfidf.toarray()
	# U,S,V=np.linalg.svd(weight)
	# for i in word:
	# 	f.write(i.encode('utf-8')+',')
	# f.write('\n')
	# for i in U:#sorted(words.iteritems(), key=lambda a:a[1], reverse=True):
	# 	f.write(repr(max(i))+','+repr(min(i)))
	# 	f.write('\n')
	# pca = PCA(n_components=20)
	# pca.fit(weight)
	# print pca.explained_variance_ratio_

	# f.close()


# def kws_sextract():
# 	import numpy as np
# 	from sklearn import feature_extraction
# 	from sklearn.feature_extraction.text import TfidfTransformer
# 	from sklearn.feature_extraction.text import CountVectorizer
# 	docs = []
# 	for i in db.item.find():
# 		if not i.get('des'):
# 			continue
# 		segs = jieba.cut(i['des'], cut_all=False)
# 		words = []
# 		for seg in segs:
# 			if seg not in stopwords and seg != ' ':
# 				words.append(seg)#words[seg] = 1 if seg not in words else words[seg]+1
# 		docs.append(' '.join(words))
# 	vectorizer = CountVectorizer()
# 	transformer = TfidfTransformer()
# 	tfidf = transformer.fit_transform(vectorizer.fit_transform(docs))
# 	word = vectorizer.get_feature_names()  #所有文本的关键字
# 	word = np.array(word)
# 	weight = tfidf.toarray()
# 	m = np.sort(weight)[:,-2::-1]
# 	with open('res.txt', 'w+') as f:
# 		for i in range(0,m.shape[0]):
# 			if m[i][0] == 0:
# 				continue
# 			res = ''
# 			for j in word[weight[i] == m[i][0]]:
# 				res = res+j+','
# 			f.write(res.encode('utf-8')+'\n')

# def userPre(uid):
# 	pre = {'_id':ObjectId(uid),'source':{},'category':{},'visited':[],'favorite':[],'wd':{},'count':1}
# 	pre['timestamp'] = datetime.datetime.now()
# 	# get the latesttime 
# 	latest = db.behavior.find({'uid':ObjectId(uid)})\
# 		.sort('timestamp', pymongo.DESCENDING).limit(1)
# 	if latest.count() > 0:
# 		latesttime = latest[0]['timestamp']
# 	else :
# 		db.upre.save(pre)
# 		return pre
# 	# deal with search behavior
# 	behaviorlist = db.behavior.find({'uid':ObjectId(uid), 'action':'search'})\
# 		.sort('timestamp', pymongo.DESCENDING).limit(1000)
# 	if behaviorlist.count() > 0:
# 		for i in behaviorlist:
# 			# calculate timefactor 1 / (1 + exp( deltaT - 10))
# 			deltaT = latesttime - i['timestamp']
# 			timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
# 			if i['ttype'] == 'source':
# 				pre['source'][i['target']] = pre['source'].get(i['target'], 0) + 1 * timefactor
# 			elif i['ttype'] == 'category':
# 				pre['category'][i['target']] = pre['category'].get(i['target'], 0) + 1 * timefactor
# 			elif i['ttype'] == 'wd':
# 				segs = jieba.cut(filter(charfilter, i['target']), cut_all=False)
# 				segs = map(lambda a: a, segs)
# 				for seg in segs:
# 					if seg not in stopwords:
# 						pre['wd'][seg] = pre['wd'].get(seg, 0) + 3. * timefactor / len(segs)
# 	# deal with click item behavior
# 	times = {}
# 	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'click', 'ttype':'item'})\
# 			.sort('timestamp', pymongo.DESCENDING).limit(500):
# 		times[i['target']] = i['timestamp']
# 		pre['visited'].append(ObjectId(i['target']))
# 	itemlist = db.item.find({'_id':{'$in':pre.get('visited',[])}})
# 	if itemlist.count() > 0:			
# 		for i in itemlist:
# 			deltaT = latesttime - times[str(i['_id'])]
# 			timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
# 			pre['count'] += 1
# 			pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.2 * timefactor
# 			# pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.2 * timefactor
# 			if i.get('title'):
# 				segs = jieba.cut(filter(charfilter, i['title']), cut_all=False)
# 				segs = map(lambda a: a, segs)
# 				for seg in segs:					
# 					if seg not in stopwords:
# 						pre['wd'][seg] = pre['wd'].get(seg, 0) + 2. * timefactor / len(segs)
# 			# if i.get('des'):
# 			# 	segs = jieba.cut(filter(charfilter, i['des']), cut_all=False)
# 			# 	segs = map(lambda a: a, segs)
# 			# 	for seg in segs:					
# 			# 		if seg not in stopwords:
# 			# 			pre['wd'][seg] = pre['wd'].get(seg, 0) + 0.4 * timefactor / len(segs)
# 	# deal with addfavorite to item behavior
# 	times = {}
# 	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'addfavorite', 'ttype':'item'})\
# 			.sort('timestamp', pymongo.DESCENDING).limit(500):
# 		times[i['target']] = i['timestamp']
# 		pre['favorite'].append(ObjectId(i['target']))
# 	itemlist = db.item.find({'_id':{'$in':pre.get('favorite',[])}})
# 	if itemlist.count() > 0:
# 		for i in itemlist:
# 			deltaT = latesttime - times[str(i['_id'])]
# 			timefactor = 1 / (1 + math.exp((deltaT.total_seconds()/24/3600.) - 60.))
# 			pre['count'] += 1
# 			pre['source'][i['source']] = pre['source'].get(i['source'], 0) + 1.5 * timefactor
# 			pre['category'][i['category']] = pre['category'].get(i['category'], 0) + 1.5 * timefactor
# 			if i.get('title'):
# 				segs = jieba.cut(filter(charfilter, i['title']), cut_all=False)
# 				segs = map(lambda a: a, segs)
# 				for seg in segs:
# 					if seg not in stopwords:
# 						pre['wd'][seg] = pre['wd'].get(seg, 0) + 3. * timefactor / len(segs)
# 			# if i.get('des'):
# 			# 	segs = jieba.cut(filter(charfilter, i['des']), cut_all=False)
# 			# 	segs = map(lambda a: a, segs)
# 			# 	for seg in segs:
# 			# 		if seg not in stopwords:
# 			# 			pre['wd'][seg] = pre['wd'].get(seg, 0) + 0.6 * timefactor / len(segs)
# 	db.upre.save(pre)
# 	return pre