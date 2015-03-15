# -*- coding: utf-8 -*-
# import pymongo
# conn = pymongo.Connection('54.187.240.68')
# db = conn['feed']
# db.authenticate('JKiriS','910813gyb')

# upre = db.upre.find_one({'visited':{'$ne':[]}})
# vitemids = upre['visited'][-100:]

# texts_origin = []
# for i in db.item.find({'_id':{'$in':vitemids}}):
#     segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
#     segs *= 2
#     segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
#     texts_origin.append(segs)

# from gensim import corpora, models, similarities
# lsi = models.LsiModel.load('G:/dav/rsbackend/gs.lsi')
# dic = corpora.Dictionary.load('G:/dav/rsbackend/gs.dic')
# index = similarities.MatrixSimilarity.load('G:/dav/rsbackend/gs.index')
# res = None
# for i in texts_origin:
#     test_bow = dic.doc2bow(i)
#     test_lsi = lsi[test_bow]
#     res = index[test_lsi] if res == None else res + index[test_lsi]
# res /= max(res)
import json

# cs = json.load(file('categories.json'))

# categories = []
# categories.append(cs['name'])
# m = {}
# for c in cs['children']:
# 	categories.append(c['name'])
# 	if 'children' in c:
# 		for cc in c['children']:
# 			m[cc['name']] = c['name']
# nf = open('cs.json', 'w+')
# json.dump(categories, nf)


import pymongo
import datetime
conn = pymongo.Connection('54.187.240.68') #
db = conn['feed']
db.authenticate('JKiriS','910813gyb')
# for i in m:
# 	# db.site.update({'category':i}, {'$set':{'category':m[i]}}, multi=True)
# 	# db.item.update({'category':i}, {'$set':{'category':m[i]}}, multi=True)
# 	db.behavior.update({'ttype':'category','target':i}, {'$set':{'category':None,'target':m[i]}}, multi=True)
# db.behavior.update({'action':'click','ttype':'item'},{'$set':{'action':'clickitem'}},multi=True)
# db.behavior.update({'action':'search','ttype':'source'},{'$set':{'action':'visitsource'}},multi=True)
# db.behavior.update({'action':'search','ttype':'category'},{'$set':{'action':'visitcategory'}},multi=True)
# db.behavior.update({'action':'search','ttype':'wd'},{'$set':{'action':'search'}},multi=True)
cs = json.load(file('cs.json'))
t = datetime.datetime.now() - datetime.timedelta(days=60)
print db.item.find({'pubdate':{'$gt':t}}).count()
for c in cs:
	print c, db.item.find({'category':c,'pubdate':{'$gt':t}}).count()
