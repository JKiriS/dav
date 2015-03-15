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

cs = json.load(file('categories.json'))
def aa(f, s):
	print s + f['name']
	if 'children' in f:
		for c in f['children']:
			aa(c, s + '\t')
aa(cs, '')
