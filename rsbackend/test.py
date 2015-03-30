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
import os
# cs = json.load(file('categories.json'))
# m = {}
# categories = []
# categories.append(cs['name'])
# for c in cs['children']:
# 	categories.append(c['name'])
# 	if 'children' in c:
# 		for cc in c['children']:
# 			m[cc['name']] = c['name']
# conn = pymongo.Connection('54.187.240.68') #
# db = conn['feed']
# db.authenticate('JKiriS','910813gyb')
# for i in m:
# 	db.site.update({'category':i}, {'$set':{'category':m[i]}}, multi=True)
# 	db.item.update({'category':i}, {'$set':{'category':m[i]}}, multi=True)
	# db.behavior.update({'ttype':'category','target':i}, {'$set':{'category':None,'target':m[i]}}, multi=True)
# db.behavior.update({'action':'click','ttype':'item'},{'$set':{'action':'clickitem'}},multi=True)
# db.behavior.update({'action':'search','ttype':'source'},{'$set':{'action':'visitsource'}},multi=True)
# db.behavior.update({'action':'search','ttype':'category'},{'$set':{'action':'visitcategory'}},multi=True)
# db.behavior.update({'action':'search','ttype':'wd'},{'$set':{'action':'search'}},multi=True)
cs = json.load(file('cs.json'))
# t = datetime.datetime.now() - datetime.timedelta(days=60)
# print db.item.find({'pubdate':{'$gt':t}}).count()
# for c in cs:
# 	print c, db.item.find({'category':c,'pubdate':{'$gt':t}}).count()
# for c in cs:
	# os.makedirs('lsiindex/'+c)
# for c in cs:
# 	print db.item.find({'_id':{'$in':db.upre.find()[2]['visits']},'category':c}).count()
# lsiindexdir = 'lsiindex'
# dic = None

# from django.http import QueryDict
# q = QueryDict('a=1')
# print q.getlist('a', [])

# for c in cs:
# 	db.category.insert({'name':c, 'visit_num':0})
# s = paramiko.SSHClient()
# s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# s.load_system_host_keys()
# s.connect(hostname, port, username, pkey=key)
# stdin, stdout, stderr = s.exec_command('ls')
# print stdout.read()
# s.close()
# t = paramiko.Transport(('54.187.240.68', 22))
# t.connect(username = 'ubuntu', pkey=key)
# sftp = paramiko.SFTPClient.from_transport(t)
# remotedir = '/home/ubuntu/dav/rsbackend/lsiindex'
# lsiindexdir = 'lsiindex'
# # for c in cs:
# # 	lpath = lsiindexdir + '/' + c
# # 	rpath = remotedir + '/' + c
# sftp.put('lsiindex/t/gs.lsi', '/home/ubuntu/gs.lsi')
# t.close()

# conn = pymongo.Connection('54.187.240.68') #
# db = conn['feed']
# db.authenticate('JKiriS','910813gyb')

# conn1 = pymongo.Connection()
# db1 = conn1['feed']
# db1.authenticate('JKiriS','910813gyb')

# for v in db.verification.find():
# 	db1.verification.insert(v)

# for v in db.verification.find():
# 	if isinstance(v['option'][0], int):
# 		for i in range(3):
# 			v['option'][i] = cs[v['option'][i]]
# 	db.verification.save(v)

# flock = open('write.lock','w+')
# flock.close()
# import os
# print os.path.isfile('write.lock1')

import jobmanager
import types
for i in dir(jobmanager):
	attr = getattr(jobmanager, i)
	if type(attr) == types.ClassType and issubclass(attr, jobmanager.Job) \
		and hasattr(attr, 'run'):
		print i

import feeds
for i in dir(feeds):
	attr = getattr(feeds, i)
	if type(attr) == types.ClassType and issubclass(attr, feeds.Parser) \
		and hasattr(attr, 'parse'):
		print attr	