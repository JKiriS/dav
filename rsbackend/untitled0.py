# -*- coding: utf-8 -*-
"""
Created on Fri Dec 12 10:07:50 2014

@author: ISE
"""
import jieba
import pymongo
conn = pymongo.Connection()
db = conn['feed']
db.authenticate('JKiriS','910813gyb')
stopwords = {}.fromkeys([ line.rstrip().decode('utf-8')\
    for line in open('e:/dav/rsbackend/stopwords.txt') ])
texts_origin = []
for i in db.item.find().limit(3000):
    segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
    segs *= 2
    segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
    texts_origin.append(segs)
all_tokens = sum(texts_origin, [])
token_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in token_once] for text in texts_origin]

from gensim import corpora, models, similarities
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
tfidf = models.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]
lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=30)
index = similarities.MatrixSimilarity(lsi[corpus])

#test_bow = dictionary.doc2bow(texts[0])
#test_lsi = lsi[test_bow]
#sims = index[test_lsi]
#sorted(enumerate(sims), key=lambda item: -item[1])