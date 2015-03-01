##---(Wed May 14 21:34:38 2014)---
import os
a=os.walk()
a=os.walk('E:/CloudMusic')
a
print a 
os.walk('E:/CloudMusic')
os.rename('E:/CloudMusic/Andy McKee/Andy McKee - Rylynn.mp3',E:/CloudMusic/Andy McKee - Rylynn.mp3)
os.rename('E:/CloudMusic/Andy McKee/Andy McKee - Rylynn.mp3','E:/CloudMusic/Andy McKee - Rylynn.mp3')
a='12235.mp3'
a[-3:]

##---(Wed Sep 03 16:30:32 2014)---
def f(x):
    return x**3 - 6*x + 3
from scipy import optimize
from matplotlib import plt
import matplotlib.pyplot as plt
import numpy as np
x = np.arange(-10, 10, 0.1)
plt.plot(x, f(x))
rppt = optimize.fsolve(f, 0.75)
root = optimize.fsolve(f, 0.75)
print root
print f(0.5239764)

##---(Thu Sep 11 12:25:58 2014)---
print 0**3
def f(y):
    if y >= 0:
        return 1-(1-y)*2*(y+4)/5/(y+3)
    else :
        y3 = (y+1)**3
        return (1/3+(2*y*y-y-3)*y3/30)/(1+(y-3)*y3/6)
f(-1)
(-1+1)**3
def f(y):
...     if y >= 0:
...         return 1-(1-y)*2*(y+4)/5/(y+3)
...     else :
...         y3 = (y+1)**3
...         return (1/3+(2*y*y-y-3)*y3/30)/(1+(y-3)*y3/6)
print 1/3
y=-1
print (2*y*y-y-3)/30+1/3
y3 = (y+1)**3
((2*y*y-y-3)*y3/30+1/3)/((y-3)*y3/6+1)
def f(y):
    if y >= 0:
        return 1-(1-y)*2*(y+4)/5/(y+3)
    else :
        y3 = (y+1)**3
        return ((2*y*y-y-3)*y3/30+1/3)/((y-3)*y3/6+1)
f(-1.)
y = np.linspace(-1, 1, 201)
z = [f(i) for i in y]
plt.plot(y, z)
plt.show()
z
plt.plot(y, z)
plt.show()

##---(Fri Dec 12 09:55:20 2014)---
import pymongo
conn = pymongo.Connection()
db.conn['feed']
db = conn['feed']
texts_origin = []
db.authenticate('JKiriS','910813gyb')
stopwords = {}.fromkeys([ line.rstrip().decode('utf-8') for line in open('e:/dav/rsbackend/stopwords.txt') ])
for i in db.item.find().limit(500):
import jieba
for i in db.item.find().limit(500):
    segs = map(lambda s:s, jieba.cut(i['title'], cut_all=False))
    segs = filfilterfor i in db.item.find().limit(500): ...     segs = map(lambda s:s, jieba.cut(i['title'], cut_all=False)) ...     segs = filfilter
[1,2,3]*2
[1,2,3] + [1]
texts_origin[0]
sum([1,2],[])
sum([[1],[2]],[])
texts[0]
from gensim import corpora, models, similarities

##---(Fri Dec 12 15:15:11 2014)---
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
tfidf = models.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]
lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=30)
first_bow = dictionary.doc2bow(texts[0])
first_lsi = lsi[first_bow]
print first_lsi
sims = index[first_lsi]
index = similarities.MatrixSimilarity(lsi[corpus])
sims = index[first_lsi]
 sort_sims = sorted(enumerate(sims), key=lambda item: -item[1])
sort_sims = sorted(enumerate(sims), key=lambda item: -item[1])
print sort_sims
first = dicionary.doc2bow(texts[0])
first = dictionary.doc2bow(texts[0])
first_lsi = lsi[first]
sims = index[first_lsi]
sorted(enumerate(sims), key=lambda item: -item[1])

##---(Fri Dec 19 09:52:26 2014)---
from gensim import corpora, models, similarities
dic = corpora.Dictionary()
dic.load('gs.dic')
dic.load('G:/dav/rsbackend/gs.dic')
index = similarities.MatrixSimilarity()
index = similarities.MatrixSimilarity.load('G:/dav/rsbackend/gs.lsi')
test_bow = dictionary.doc2bow('Google')
test_bow = dic.doc2bow('Google')
test_bow = dic.doc2bow(['Google'])
lsi = models.LsiModel()
lsi = models.LsiModel.load('G:/dav/rsbackend/gs.lsi')
lsi[test_bow]
lsi = models.LsiModel.load('G:/dav/rsbackend/gs.lsi.projection')
lsi = models.LsiModel.load('G:/dav/rsbackend/gs.lsi')
lsi[test_bow]
test_bow
test_bow = dic.doc2bow(['Facebook'])
test_bow
test_bow = dic.doc2bow(['阿里巴巴'])
test_bow = dic.doc2bow([u'阿里巴巴'])
test_bow
test_bow = dic.doc2bow(['aws'])
test_bow
dic
dic.values()
dic.keys()
dic = corpora.Dictionary.load('G:/dav/rsbackend/gs.dic')
dic.keys()
test_bow = dic.doc2bow([u'阿里巴巴'])
test_bow
test_bow = dic.doc2bow(['Google'])
test_bow
lsi[test_bow]
sims = index[test_lsi]
test_lsi = lsi[test_bow]
sims = index[test_lsi]
sorted(enumerate(sims), key=lambda item: -item[1])[10]
sorted(enumerate(sims), key=lambda item: -item[1])
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
test_bow = dic.doc2bow([u'马云'])
test_bow
test_bow = dic.doc2bow(['马云'])
import pymongo
conn = pymongo.Connection()
db = conn['feed']
db.authenticate('JKiriS','910813gyb')
test_bow = dic.doc2bow(['马云'])
test_item = db.item.find_one()
segs = filter(lambda s:s not in stopwords, jieba.cut(test_item['title'], cut_all=False))
import jieba
segs = filter(lambda s:s not in stopwords, jieba.cut(test_item['title'], cut_all=False))
segs = filter(lambda s: True, jieba.cut(test_item['title'], cut_all=False))
segs
test_bow = dic.doc2bow(segs)
test_bow
test_lsi = lsi[test_bow]
sims = index[test_lsi]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
test_lsi
conn = pymongo.Connection('54.187.240.68')
db = conn['feed']
db.authenticate('JKiriS','910813gyb')
upre = db.upre.find_one({'count':{'$gt':1}})
vitemids = upre['visited'][-50:]
upre = db.upre.find_one({'visited':{'$ne':[]}})
vitemids = upre['visited'][-50:]
stopwords = {}.fromkeys([ line.rstrip().decode('utf-8')\
    for line in open('e:/dav/rsbackend/stopwords.txt') ])
texts_origin = []
vitemids[1]
for i in db.item.find({'_id':{'$in':vitemids}}):
    segs = filter(lambda s:s not in stopwords, jieba.cut(i['title'], cut_all=False))
    segs *= 2
    segs += filter(lambda s:s not in stopwords, jieba.cut(i['des'], cut_all=False))
    texts_origin.append(segs)
texts_origin[1]
test_bow = dictionary.doc2bow(texts_origin[0])
test_bow = dic.doc2bow(texts_origin[0])
test_lsi = lsi[test_bow]
test_lsi
sims = index[test_lsi]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
vitemids[0]
texts_origin[0]
db.item.find({'_id':{'$in':vitemids}}).limit(1)
db.item.find_one({'_id':{'$in':vitemids}})['_id']
test_bow
dic[8]
dic[8].encode('utf-8')
dic[8].decode('utf-8')
str(dic[8])
repr(dic[8])
index = similarities.MatrixSimilarity.load('G:/dav/rsbackend/gs.index')
sims = index[test_lsi]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
for t in texts_origin:
    test_bow = dic.doc2bow(i)
    test_lsi = lsi[test_bow]
visited_lsi = []
for t in texts_origin:
...     test_bow = dic.doc2bow(i)
...     test_lsi = lsi[test_bow]
for t in texts_origin:
    test_bow = dic.doc2bow(i)
    test_lsi = lsi[test_bow]
    visited_lsi.append(test_lsi)
len(visited_lsi)
visited_lsi[0]
visited_lsi[1]
sum(visited_lsi[0],key=lambda a:a[1])
reduce(lambda a,b:a+b[1],visited_lsi[0],0)
index[visited_lsi[1]]
sims = index[visited_lsi[1]]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
for t in texts_origin:
    test_bow = dic.doc2bow(t)
    test_lsi = lsi[test_bow]
    visited_lsi.append(test_lsi)
sims = index[visited_lsi[1]]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
visited_lsis = []
for t in texts_origin:
    test_bow = dic.doc2bow(t)
    test_lsi = lsi[test_bow]
    visited_lsis.append(test_lsi)
del visited_lsi
sims = index[visited_lsis[1]]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
sims = index[visited_lsis[0]]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
sims = index[visited_lsis[2]]
sorted(enumerate(sims), key=lambda item: -item[1])[:10]
visited_lsis[0]
visited_lsis[1]
visited_lsis[2]
from sklearn.cluster import KMeans