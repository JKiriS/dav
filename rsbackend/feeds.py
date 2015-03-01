#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
import urllib2
from bs4 import BeautifulSoup
import feedparser
import datetime, time
import re
import json
import urlparse
import random

import socket
socket.setdefaulttimeout(20)

sites = [
		{'url':'http://cnbeta.feedsportal.com/csite/34306/f/624776/index.rss', 'source':'cnBeta', 'category':'互联网'},
		{'url':'http://feed.mtime.com/movienews.rss', 'source':'时光网', 'category':'电影'},
		{'url':'http://feed.mtime.com/tvnews.rss', 'source':'时光网', 'category':'剧集'},
		{'url':'http://feed.mtime.com/videonews.rss', 'source':'时光网', 'category':'视频'},
		{'url':'http://feed.mtime.com/peoplenews.rss', 'source':'时光网', 'category':'影星'},
		{'url':'http://feed.mtime.com/comment.rss', 'source':'时光网', 'category':'电影'},
		{'url':'http://news.163.com/special/00011K6L/rss_gn.xml', 'source':'网易新闻', 'category':'国内'},
		{'url':'http://news.163.com/special/00011K6L/rss_gj.xml', 'source':'网易新闻', 'category':'国际'},
		{'url':'http://news.163.com/special/00011K6L/rss_war.xml', 'source':'网易新闻', 'category':'军事'},
		{'url':'http://ent.163.com/special/00031K7Q/rss_toutiao.xml', 'source':'网易新闻', 'category':'娱乐'},
		{'url':'http://money.163.com/special/00252EQ2/toutiaorss.xml', 'source':'网易新闻', 'category':'经济'},
		{'url':'http://money.163.com/special/00252LIB/cjztrss.xml', 'source':'网易新闻', 'category':'金融'},
		{'url':'http://money.163.com/special/00252EQ2/yaowenrss.xml', 'source':'网易新闻', 'category':'经济'},
		{'url':'http://money.163.com/special/00252EQ2/macrorss.xml', 'source':'网易新闻', 'category':'经济'},
		{'url':'http://mobile.163.com/special/001144R8/mirss.xml', 'source':'网易新闻', 'category':'互联网'},
		{'url':'http://mobile.163.com/special/001144R8/mobile163_copy.xml', 'source':'网易新闻', 'category':'移动'},
		{'url':'http://mobile.163.com/special/001144R8/mdrss.xml', 'source':'网易新闻', 'category':'移动'},
		{'url':'http://daxue.163.com/special/00913J5N/daxuerss.xml', 'source':'网易新闻', 'category':'教育'},
		{'url':'http://edu.163.com/special/002944N7/edunews0126.xml', 'source':'网易新闻', 'category':'教育'},
		{'url':'http://www.csdn.net/article/rss_lastnews', 'source':'CSDN', 'category':'科技'},
		{'url':'http://cloud.csdn.net/rss_cloud.html', 'source':'CSDN', 'category':'云计算'},
		{'url':'http://mobile.csdn.net/rss_mobile.html', 'source':'CSDN', 'category':'科技'},
		{'url':'http://sd.csdn.net/rss_sd.html', 'source':'CSDN', 'category':'软件'},
		{'url':'http://feed.cnblogs.com/blog/picked/rss', 'source':'博客园', 'category':'科技'},
		{'url':'http://www.guokr.com/rss/', 'source':'果壳', 'category':'科技'},
		{'url':'http://www.scipark.net/feed/', 'source':'科技公园', 'category':'科学'},
		{'url':'http://blog.sina.com.cn/rss/1286528122.xml', 'source':'新浪博客', 'category':'科技'},
		{'url':'http://songshuhui.net/feed', 'source':'科学松鼠会', 'category':'科技', 'parser':'imgInContent'},
		{'url':'http://pansci.tw/feed', 'source':'泛科学', 'category':'科技'},
		{'url':'http://feeds.geekpark.net/', 'source':'极客公园', 'category':'科技', 'parser':'desImgInContent'},
		{'url':'http://www.36kr.com/feed', 'source':'36氪', 'category':'科技', 'parser':'imgInDes'},  #contains img
		{'url':'http://9.douban.com/rss/technology', 'source':'豆瓣九点', 'category':'科技'},
		{'url':'http://www.alibuybuy.com/feed', 'source':'互联网的那点事', 'category':'互联网'},
		{'url':'http://www.ftchinese.com/rss/news', 'source':'FT中文网', 'category':'综合'},
		{'url':'http://www.ftchinese.com/rss/column/007000005', 'source':'FT中文网', 'category':'综合'},
		{'url':'http://www.ftchinese.com/rss/hotstoryby7day', 'source':'FT中文网', 'category':'综合'},
		{'url':'http://www.ibm.com/developerworks/cn/views/global/rss/libraryview.jsp?end=50', 'source':'IBM', 'category':'科技'},
		{'url':'http://feed.williamlong.info/', 'source':'月光博客', 'category':'科技'},
		{'url':'http://www.leiphone.com/feed/', 'source':'雷锋网', 'category':'科技', 'parser':'imgInDes'}, # contains img
		{'url':'http://www.infoq.com/cn/rss/rss.action?token=yV5lHoM3uVZTqXcuTdyeDFK4uzcE6XNQ', 'source':'infoQ', 'category':'科技'},
		{'url':'http://movie.douban.com/feed/review/movie', 'source':'豆瓣电影', 'category':'电影'},  
		{'url':'http://www.zhihu.com/rss', 'source':'知乎', 'category':'综合'},
		{'url':'http://news.163.com/special/00011K6L/rss_newsattitude.xml', 'source':'网易新闻', 'category':'综合'},
		{'url':'http://cn.engadget.com/rss.xml', 'source':'Engadget', 'category':'科技', 'parser':'imgInDes'},  #contains img
		{'url':'http://blog.163.com/cbn.weekly/rss/', 'source':'第一财经', 'category':'金融'},
		{'url':'http://www.xiami.com/collect/feed', 'source':'虾米音乐', 'category':'音乐', 'parser':'imgInDes'}, #contains img
		{'url':'http://cn.technode.com/feed/', 'source':'动点科技', 'category':'科技'},
		{'url':'http://cnpolitics.org/feed/', 'source':'政见', 'category':'政治'},
		{'url':'http://content.businessvalue.com.cn/feed', 'source':'商业价值', 'category':'商业'},
		{'url':'http://feed.yeeyan.org/culture', 'source':'译言网', 'category':'文化', 'parser':'desImgInContent'},
		{'url':'http://feed.yeeyan.org/society', 'source':'译言网', 'category':'社会', 'parser':'desImgInContent'},
		{'url':'http://feed.yeeyan.org/business', 'source':'译言网', 'category':'商业',  'parser':'desImgInContent'},
		{'url':'http://www.ifanr.com/feed', 'source':'爱范儿', 'category':'科技', 'parser':'ifanr'}, # contains img
		{'url':'http://www.199it.com/feed', 'source':'199it', 'category':'数据'},
		{'url':'https://pt.sjtu.edu.cn/torrentrss.php?rows=10&cat401=1&cat402=1&cat403=1'+\
			'&cat406=1&cat407=1&cat408=1&cat409=1&cat410=1&cat420=1&cat421=1&cat422=1&cat423=1'+\
			'&cat425=1&cat427=1&cat429=1&cat431=1&cat434=1&cat435=1&cat451=1', 'source':'葡萄', 'category':'综合'},
		{'url':'http://www.poboo.com/feed', 'source':'poboo', 'category':'艺术'},
		{'url':'http://www.itongji.cn/rss.php', 'source':'中国统计网', 'category':'数据'},
		{'url':'http://blog.ted.com/feed/', 'source':'TED', 'category':'综合', 'parser':'imgInContent'},
		{'url':'http://www.woshipm.com/feed', 'source':'人人都是产品经理', 'category':'产品', 'parser':'imgInContent'},
		{'url':'http://blog.data-god.com/?feed=rss2', 'source':'魔镜', 'category':'数据', 'parser':'desImgInContent'},
		{'url':'http://www.pmtoo.com/rss.php', 'source':'产品中国', 'category':'互联网', 'parser':'imgInDes'},
		{'url':'http://technews.cn/feed/', 'source':'科技新报', 'category':'科技', 'parser':'desImgInContent'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=86&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'娱乐', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=105&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'音乐', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=104&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'音乐', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=95&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'篮球', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=94&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'足球', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=70&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'科技', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=96&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'电影', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=97&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'剧集', 'parser':'acfun'},
		{'url':'http://www.acfun.tv/rank.aspx?channelId=106&range=1&count=30&ext=1&date=', 'source':'acfun', 'category':'动画', 'parser':'acfun'},
		{'url':'http://www.huxiu.com/rss/0.xml', 'source':'虎嗅网', 'category':'商业', 'parser':'imgInDes'},
		{'url':'http://www.huxiu.com/rss/1.xml', 'source':'虎嗅网', 'category':'商业', 'parser':'imgInDes'},
		{'url':'http://www.huxiu.com/rss/4.xml', 'source':'虎嗅网', 'category':'商业', 'parser':'imgInDes'},
		{'url':'http://www.tmtpost.com/feed?cat=-1204', 'source':'钛媒体', 'category':'科技', 'parser':'desImgInContent'},
		{'url':'http://news.ifeng.com/rss/index.xml', 'source':'凤凰新闻', 'category':'综合',},
		{'url':'http://bbs.whnet.edu.cn/xml/posttop10.xml', 'source':'华科大bbs', 'category':'综合', 'parser':'hustBBS'},
		{'url':'http://flowingdata.com/feed/', 'source':'FlowingData', 'category':'数据', 'parser':'desImgInContent'},
		{'url':'http://www.51cto.com/php/rss1.php?typeid=15', 'source':'51CTO', 'category':'云计算',},
		{'url':'http://www.51cto.com/php/rss1.php?typeid=583', 'source':'51CTO', 'category':'移动',},
		{'url':'http://onehd.herokuapp.com/', 'source':'一个', 'category':'文化'},
		{'url':'http://each.fm/live/53c6d726d01983e704000008/rss.xml', 'source':'谷奥', 'category':'科技', 'parser':'imgInDes'},
		{'url':'http://www.huangjiwei.com/blog/?feed=rss2', 'source':'孤岛客', 'category':'综合', 'parser':'imgInContent'},
		{'url':'http://www.kdatu.com/feed/', 'source':'看大图', 'category':'娱乐', 'parser':'desImgInContent'},
		{'url':'http://movie.douban.com/feed/review/movie_new', 'source':'豆瓣电影', 'category':'电影'},
		{'url':'https://news.google.com/news?pz=1&cf=all&ned=cn&hl=zh-CN&topic=w&output=rss', 'source':'google', 'category':'国际', 'parser':'googlenews'},
		{'url':'https://news.google.com/news/feeds?pz=1&cf=all&ned=cn&hl=zh-CN&topic=n&output=rss', 'source':'google', 'category':'国内', 'parser':'googlenews'},
		{'url':'https://news.google.com/news/feeds?pz=1&cf=all&ned=cn&hl=zh-CN&topic=e&output=rss', 'source':'google', 'category':'娱乐', 'parser':'googlenews'},
		{'url':'https://news.google.com/news/feeds?pz=1&cf=all&ned=cn&hl=zh-CN&topic=s&output=rss', 'source':'google', 'category':'体育', 'parser':'googlenews'},
		{'url':'https://news.google.com/news?pz=1&cf=all&ned=cn&hl=zh-CN&topic=t&output=rss', 'source':'google', 'category':'科技', 'parser':'googlenews'},
		{'url':'https://news.google.com/news/feeds?pz=1&cf=all&ned=cn&hl=zh-CN&topic=b&output=rss', 'source':'google', 'category':'经济', 'parser':'googlenews'},
		{'url':'http://www.socialbeta.com/feed', 'source':'socialbeta', 'category':'科技', 'parser':'imgInDes'},
		{'url':'http://tech2ipo.feedsportal.com/c/34822/f/641707/index.rss', 'source':'创见', 'category':'科技', 'parser':'desImgInContent'},
		{'url':'http://cos.name/feed/', 'source':'统计之都', 'category':'数据', 'parser':'desImgInContent'},
		{'url':'http://blog.talkingdata.net/?feed=rss2', 'source':'TalkingData', 'category':'数据'},
		{'url':'http://blog.csdn.net/v_july_v/rss/list', 'source':'CSDN', 'category':'数据'},
		{'url':'http://vis.pku.edu.cn/blog/feed/', 'source':'北大可视化分析', 'category':'数据', 'parser':'desImgInContent'},
		{'url':'http://zaobao.feedsportal.com/c/34003/f/616934/index.rss', 'source':'联合早报', 'category':'综合'},
		{'url':'http://jiaren.org/feed/', 'source':'佳人', 'category':'文化', 'parser':'desImgInContent'},
		{'url':'http://blog.sina.com.cn/rss/sciam.xml', 'source':'环球科学', 'category':'科学', 'parser':'imgInDes'},
		{'url':'http://www.movies.com/rss-feeds/movie-news-rss', 'source':'Movies', 'category':'电影'},
		{'url':'http://www.apollo-magazine.com/feed/', 'source':'Apollo Magazine', 'category':'艺术', 'parser':'desImgInContent'},
		{'url':'http://www.adaymag.com/feed/', 'source':'時尚生活雜誌', 'category':'生活'},
		{'url':'http://cinephilia.net/feed', 'source':'迷影', 'category':'电影'},
		{'url':'http://hanhanone.sinaapp.com/feed/dajia', 'source':'大家', 'category':'文化', 'parser':'imgInDes'},
		{'url':'http://iwucha.com/feed/', 'source':'爱午茶创意坊', 'category':'文化', 'parser':'desImgInContent'},
		{'url':'http://www.dfdaily.com/rss/1170.xml', 'source':'上海书评', 'category':'读书', 'parser':'imgInDes'},
		{'url':'http://www.pento.cn/timeline/top_v2/pins/list.html?offset=0&count=50', 'source':'品读', 'category':'综合', 'parser':'pento'},
	]

now = lambda : datetime.datetime.now()

def simplerss(i, site):
	rss = {}
	try:
		rss['pubdate'] = now() if i.get('published_parsed') == None else \
			datetime.datetime.fromtimestamp( time.mktime(i['published_parsed']) )
		if site.get('latest') and rss['pubdate'] <= site['latest']:
			return None
		rss['source'] = site['source']
		rss['tags'] = []
		rss['category'] = site['category']
		for t in i.get('tags', []):
			if t.term not in rss['tags']:
				rss['tags'].append(t.term)
		rss['title'] = i['title']
		rss['link'] = i['link']
	except Exception, e:
		print e
	return rss

def common(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None:
			if 'summary_detail' in i:
				des = i['summary_detail']['value']
				soup = BeautifulSoup(des)
				rss['des'] = soup.get_text()
				if len(rss['des']) >= 500:
					rss['des'] = rss['des'][:500]+'...'
				rss['rand'] = [random.random(), 0]
				rsslist.append(rss)
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def ifanr(site=None):
	from xml.etree import ElementTree as ET
	rsslist = []
	rawrss = urllib2.urlopen(site['url'])
	channel = ET.parse(rawrss).find('./channel')
	for i in channel.findall('item'):
		rss = {}
		rss['pubdate'] = datetime.datetime.strptime(i.find('pubDate').text[:-6], '%a, %d %b %Y %X')
		if site.get('latest') and rss['pubdate'] <= site['latest']:
			break
		rss['source'] = site['source']
		rss['tags'] = []
		rss['category'] = site['category']
		for t in i.findall('category'):
			if t.text not in rss['tags']:
				rss['tags'].append(t.text)
		rss['title'] = i.find('title').text
		rss['link'] = i.find('link').text
		if i.find('image') != None:
			rss['imgurl'] = i.find('image').text
		des = i.find('description').text
		soup = BeautifulSoup(des)
		rss['des'] = soup.get_text()
		if len(rss['des']) >= 500:
			rss['des'] = rss['des'][:500]+'...'
		rss['rand'] = [random.random(), 0]
		rsslist.append(rss)
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def imgInDes(site=None):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None:	
			if 'summary_detail' in i:
				des = i['summary_detail']['value']
				soup = BeautifulSoup(des)
				rss['des'] = soup.get_text()
				if len(rss['des']) >= 500:
					rss['des'] = rss['des'][:500]+'...'		
				if soup.find('img'):
					rss['imgurl'] = soup.find('img').get('src')
				rss['rand'] = [random.random(), 0]
				rsslist.append(rss)
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def imgInContent(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None:
			if 'summary_detail' in i:
				des = i['summary_detail']['value']
				soup = BeautifulSoup(des)
				rss['des'] = soup.get_text()
				if len(rss['des']) >= 500:
					rss['des'] = rss['des'][:500]+'...'			
				if 'content' in i:
					soup = BeautifulSoup(i.content[0].value)
					if soup.find('img'):
						rss['imgurl'] = soup.find('img').get('src')
				rss['rand'] = [random.random(), 0]
				rsslist.append(rss)
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def desImgInContent(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None:			
			if 'content' in i:
				content = reduce(lambda a,b:a+b.value, i.content, '')
				soup = BeautifulSoup(content)
				rss['des'] = soup.get_text()
				if len(rss['des']) >= 500:
					rss['des'] = rss['des'][:500]+'...'
				if soup.find('img'):
					rss['imgurl'] = soup.find('img').get('src')
				rss['rand'] = [random.random(), 0]
				rsslist.append(rss)
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def acfun(site):
	baseurl = 'http://www.acfun.tv'
	data = urllib2.urlopen(site['url']).read()
	rsslist = []
	for i in json.loads(data):
		rss = {'source':site['source'], 'tags':[], 'category':site['category']}
		rss['link'] = baseurl + i['url']
		if db.item.find_one({'link':rss['link']}):
			continue
		rss['title'] = i['title']
		rss['des'] = i.get('description')
		rss['imgurl'] = i.get('titleImg')
		if rss['des'] and len(rss['des']) >= 500:
			rss['des'] = rss['des'][:500]+'...'	
		try:
			rss['pubdate'] = now() if not i.get('releaseDate') else \
				datetime.datetime.strptime(i.get('releaseDate'), '%Y-%m-%d %X')
		except Exception, e:
			print e
		rss['rand'] = [random.random(), 0]
		rsslist.append(rss)
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def hustBBS(site):
	html = urllib2.urlopen(site['url']).read()
	soup = BeautifulSoup(html.decode('gbk'))
	rsslist = []
	for i in soup.find_all('post'):
		rss = {'source':site['source'], 'tags':[], 'category':site['category']}
		rss['title'] = i.find('title').get_text()
		board = i.find('board').get_text()
		ifile = i.find('file').get_text()
		reply_count = i.find('reply_count').get_text()
		rss['link'] = 'http://bbs.whnet.edu.cn/cgi-bin/bbstcon?board='+board+'&file='+ifile
		rss['des'] = u'板块:'+board+u'   回复人数:'+reply_count
		rss['pubdate'] = now()
		rss['rand'] = [random.random(), 0]
		rsslist.append(rss)
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def googlenews(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = {}
		try:
			rss['pubdate'] = now() if i.get('published_parsed') == None else \
				datetime.datetime.fromtimestamp( time.mktime(i['published_parsed']) )
			rss['source'] = site['source']
			rss['tags'] = []
			rss['category'] = site['category']
			for t in i.get('tags', []):
				if t.term not in rss['tags']:
					rss['tags'].append(t.term)
			rss['title'] = i['title']
			link = urlparse.urlparse( i['link'] )
			rss['link'] = urlparse.parse_qs(link.query, True).get('url')[0]
			if 'summary_detail' in i:
				des = i['summary_detail']['value']
				soup = BeautifulSoup(des)
				rss['des'] = soup.get_text()
				if len(rss['des']) >= 500:
					rss['des'] = rss['des'][:500]+'...'
				rss['rand'] = [random.random(), 0]
				rsslist.append(rss)
		except Exception, e:
			print e
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def pento(site):
	BASE_URL = 'http://www.pento.cn'
	html = urllib2.urlopen(site['url']).read()
	soup = BeautifulSoup(html)
	rsslist = []
	for i in soup.find_all(class_='book_list_box'):
		rss = {'source':site['source'], 'tags':[], 'category':site['category']}
		titlea = i.find('div', class_='book_card_title').find('a')
		try :
			rss['title'] = titlea.get_text()
			rss['link'] = BASE_URL + titlea.get('href')
			rss['des'] = i.find('div', class_='book_card_content').get_text()
			pubdate = i.find('div', class_='book_card_time').get_text()
			rss['imgurl'] = i.find('input').get('value')
			rss['pubdate'] = datetime.datetime.strptime(pubdate, '%Y-%m-%d')
			rss['rand'] = [random.random(), 0]
			rsslist.append(rss)
		except :
			pass
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def updatesites(sites=[]):
	for i in sites:
		s = db.source.find_one({'name':i['source']})
		if s == None:
			s = {'name':i['source']}
			db.source.insert(s)
		oldi = db.site.find_one({'url':i['url']})
		if oldi != None:
			oldi.update(i)
			db.site.save(oldi)
		else :
			if 'parser' not in i:
				i['parser'] = 'common'
			db.site.save(i)

def run():
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')
	updatesites(sites)
	for i in db.site.find(timeout=False):
		try:
			exec( i['parser']+'(i)' )
		except Exception, e:
			print i['url'] + str(e)
	db.item.update({'pubdate':{'$gt':now()}}, {'$set':{'pubdate':now()}}, multi=True)
	db.site.update({'latest':{'$gt':now()}}, {'$set':{'latest':now()}}, multi=True)
	# db.job.insert({'module':'updateindex', 'starttime':now() + datetime.timedelta(minutes=10)})
	# db.job.insert({'module':'calcupre', 'starttime':now() + datetime.timedelta(minutes=5)})
	db.job.insert({'module':'feeds', 'starttime':now() + datetime.timedelta(hours=12)})
	conn.close()


if __name__ == '__main__':
	global db
	conn = pymongo.Connection()
	db = conn['feed']
	db.authenticate('JKiriS','910813gyb')	
	updatesites(sites)
	for i in db.site.find(timeout=False):
		try:
			print i['url']
			exec( i['parser']+'(i)' )
		except Exception, e:
			print i['url'] + str(e)
	db.item.update({'pubdate':{'$gt':now()}}, {'$set':{'pubdate':now()}}, multi=True)
	db.site.update({'latest':{'$gt':now()}}, {'$set':{'latest':now()}}, multi=True)
	print 'program finished'
	input()
	conn.close()


# db.item.update({category:'影评'},{$set:{category:'电影'}},{multi:true})