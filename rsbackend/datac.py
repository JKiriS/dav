# -*- coding: utf-8 -*-
import pymongo
import datetime
from bs4 import BeautifulSoup
import urlparse
import json

now = lambda : datetime.datetime.now()

def mongoconn(host='127.0.0.1'):
	conn = pymongo.Connection(host,27017)
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	return db

# db = mongoconn()

# db.item.ensureIndex({link:1},{unique:true,dropDups:true})
# db.site.ensureIndex({url:1},{unique:true})

# for i in db.item.find({'source':'ifanr'}):
# 	soup = BeautifulSoup(i['des'])
# 	i['des'] = soup.get_text()
# 	if len(i['des']) >= 500:
# 		i['des'] = i['des'][:500]+'...'
# 	db.item.save(i)

# for i in db.item.find({'pubdate':{'$gt':datetime.datetime.now()}}):
# 	i['pubdate'] = datetime.datetime.now()
# 	db.item.save(i)

# for i in db.item.find():
# 	i['category'] = i['category'][0]
# 	db.item.save(i)

# for i in db.item.find({'source':'google'}):
	# i['link'] = i['link'][0]
	# link = urlparse.urlparse(i['link'])
	# i['link'] = urlparse.parse_qs(link.query, True).get('url')
	# db.item.save(i)

# urls = []
# for i in db.site.find():
# 	print i['url']
	# if i.get('url') not in urls:
	# 	urls.append(i.get('url'))
	# else :
	# 	db.site.remove({'_id':i['_id']})

# cs = {
# 	'name':'综合',
# 	'children':
# 	[
# 		{
# 			'name':'科技',
# 			'children':
# 			[
# 				{ 'name':'互联网' },
# 				{ 'name':'移动', },
# 				{ 'name':'云计算' },
# 				{ 'name':'软件' },
# 				{ 'name':'科学' },
# 				{ 'name':'数据' },
# 				{ 'name':'产品' },
# 			]
# 		},
# 		{
# 			'name':'娱乐',
# 			'children':
# 			[
# 				{ 'name':'电影' },
# 				{ 'name':'剧集' },
# 				{ 'name':'视频' },
# 				{ 'name':'影星' },
# 				{ 'name':'音乐' },
# 				{ 'name':'动画' },
# 			]
# 		},
# 		{
# 			'name':'体育',
# 			'children':
# 			[
# 				{ 'name':'篮球' },
# 				{ 'name':'足球' },
# 			]
# 		},
# 		{
# 			'name':'文化',
# 			'children':
# 			[
# 				{ 'name':'教育' },
# 				{ 'name':'艺术' },
# 			]
# 		},
# 		{
# 			'name':'军事',
# 		},
# 		{
# 			'name':'财经',
# 			'children':
# 			[
# 				{ 'name':'经济' },
# 				{ 'name':'金融' },
# 				{ 'name':'商业' },
# 			]
# 		},
# 		{
# 			'name':'时政',
# 			'children':
# 			[
# 				{ 'name':'政治' },
# 				{ 'name':'社会' },
# 				{ 'name':'国内' },
# 				{ 'name':'国际' },
# 			]
# 		},
# 	]
# }

# import json

# with open('categories.json', 'w+') as f:
# 	f.write( json.dumps(cs) )

# csfile =  file('categories.json')
# cs = json.load(csfile)

# def cssearch(tree=cs, target=u''):
# 	if tree['name'] == target:
# 		return csgather(tree, [])
# 	else :
# 		if 'children' in tree:
# 			for i in tree['children']:
# 				res = cssearch(i, target)
# 				if len(res) > 0:
# 					return res
# 	return []

# def csgather(tree=cs, res=[]):
# 	res.append(tree['name'])
# 	if 'children' in tree:
# 		for i in tree['children']:
# 			csgather(i, res)
# 	return res

# print cssearch()
# import random
# db = mongoconn()
# for i in db.item.find():
# 	i['rand'] = [random.random(), 0]
# 	db.item.save(i)

# import string
# delStr = string.punctuation + u'《》（）&%￥#@！{}【】' + string.digits
# s = u'gdsg8754gfd2014,.gdogfjisg5u4ohgud;mgrkl/amgelj54uiwpt4iwfnmskagnme;m5i3[t4mgfdl/smgrieog'
# def filterstr(a):
# 	if a in delStr:
# 		return None
# 	return a
# print filter(filterstr ,s)

db = mongoconn('54.187.240.68')
print db.upre.find()[1].get('usegs')