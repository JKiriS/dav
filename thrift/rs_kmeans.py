# -*- coding: utf-8 -*-

import numpy as np
from sklearn import cluster, preprocessing

from recserver import *

def updateRList(uid):
	db = dbm.getprimary()
	upre = db.upre.find_one({'_id':ObjectId(uid)})
	lsi = lfm.getlsi('search')
	dic = lfm.getdic('search')
	index = lfm.getindex('search')
	itemIds = lfm.getid('search')

	oldrlist = db.rlist.find_one({'_id':ObjectId(uid)})
	oldrlist = [] if not oldrlist else oldrlist.get('rlist')

	visits = {}
	for i in db.behavior.find({'uid':ObjectId(uid), 'action':'clickitem'})\
			.sort('timestamp', pymongo.DESCENDING).limit(1000):
		visits[ObjectId(i['target'])] = 1
	upre['visits'] = visits.keys()
	db.upre.save(upre)

	data = []
	visits_ids = []
	for i in db.item.find({'_id':{'$in':visits.keys()}}):
		visits_ids.append(i['_id'])
		segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
		segs *= 2
		segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
		test_bow = dic.doc2bow(segs)
		test_lsi = lsi[test_bow]
		data.append(map(lambda a:a[1], test_lsi))
	if not visits_ids:
		res = Result()
		res.success = True
		return res
		
	data = np.array(data)

	K = 5

	# data = preprocessing.scale(data)  #  Z-Score
	# data = preprocessing.MinMaxScaler().fit_transform(data)  #  range
	# data = preprocessing.normalize(data, norm='l2')  #  l2 Normalization

	k_means = cluster.KMeans(K)
	k_means.fit(data)

	label = k_means.labels_

	label_count = {}
	for i in label:
		label_count[i] = label_count.get(i, 0) + 1

	max_label = sorted(label_count.items(), key=lambda a:a[1])[-1][0]

	score = None
	for i in range(K):
		center = list(enumerate(np.mean(data[label==i], axis=0)))
		center_score = index[center]  * label_count.get(i) / len(label)
		# score = center_score if score is None else score + center_score
		score = center_score if score is None else np.vstack((score, center_score))

	print score.shape
	score = np.amax(score, axis=0)
	print score.shape

	latestitemIds, latestitemScores = itemIds[-2000:], score[-2000:]

	latestitemScores += .2 * np.random.random(len(latestitemScores))

	res = map(list, zip(latestitemIds, latestitemScores))
	for r in res:
		if r[0] in oldrlist: 
			r[1] *= .8
		if r[0] in visits: 
			r[1] = 0
	rlist = map(lambda y:y[0], sorted(res, key=lambda y:y[1], reverse=True))

	db.rlist.save({'_id':ObjectId(uid),'rlist':rlist,'timestamp':now()})

	res = Result()
	res.success = True
	return res

if __name__ == '__main__':
	updateRList('5459d5ee7c46d50ae022b901')