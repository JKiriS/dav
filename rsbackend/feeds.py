#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
from bs4 import BeautifulSoup
import feedparser
import datetime, time
import re
import json
import urlparse
import random
import socket

PARAMS = json.load(file('../self.cfg'))

socket.setdefaulttimeout(PARAMS['feed']['timeout'])
now = lambda : datetime.datetime.now()

def simplerss(i, site):
	rss = {'click_num':0, 'favo_num':0}
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
		return None
	return rss

def saveRsslist(rsslist, site):
	if len(rsslist) > 0:
		db.item.insert(rsslist, continue_on_error=True)
		site['latest'] = rsslist[0]['pubdate']
		db.site.save(site)

def checkRss(rss):
	if 'des' not in rss or len(rss['des']) < 6:
		return False
	elif len(rss['des']) >= 500:
		rss['des'] = rss['des'][:500]+'...'
	rss['rand'] = [random.random(), 0]
	return True

def common(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None and 'summary_detail' in i:
			des = i['summary_detail']['value']
			soup = BeautifulSoup(des)
			rss['des'] = soup.get_text()
			if checkRss(rss):
				rsslist.append(rss)
	saveRsslist(rsslist, site)

def ifanr(site=None):
	from xml.etree import ElementTree as ET
	rsslist = []
	rawrss = urllib2.urlopen(site['url'])
	channel = ET.parse(rawrss).find('./channel')
	for i in channel.findall('item'):
		rss = {'click_num':0, 'favo_num':0}
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
		if checkRss(rss):
			rsslist.append(rss)
	saveRsslist(rsslist, site)

def imgInDes(site=None):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None and 'summary_detail' in i:	
			des = i['summary_detail']['value']
			soup = BeautifulSoup(des)
			rss['des'] = soup.get_text()		
			if soup.find('img'):
				rss['imgurl'] = soup.find('img').get('src')
			if checkRss(rss):
				rsslist.append(rss)
	saveRsslist(rsslist, site)

def imgInContent(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None and 'summary_detail' in i:
			des = i['summary_detail']['value']
			soup = BeautifulSoup(des)
			rss['des'] = soup.get_text()
			if 'content' in i:
				soup = BeautifulSoup(i.content[0].value)
				if soup.find('img'):
					rss['imgurl'] = soup.find('img').get('src')
			if checkRss(rss):
				rsslist.append(rss)
	saveRsslist(rsslist, site)

def desImgInContent(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = simplerss(i, site)
		if rss != None and 'content' in i:			
			content = reduce(lambda a,b:a+b.value, i.content, '')
			soup = BeautifulSoup(content)
			rss['des'] = soup.get_text()
			if soup.find('img'):
				rss['imgurl'] = soup.find('img').get('src')
			if checkRss(rss):
				rsslist.append(rss)
	saveRsslist(rsslist, site)

def acfun(site):
	baseurl = 'http://www.acfun.tv'
	data = urllib2.urlopen(site['url']).read()
	rsslist = []
	for i in json.loads(data):
		rss = {'source':site['source'], 'tags':[], 'category':site['category'], \
			'click_num':0, 'favo_num':0}
		rss['link'] = baseurl + i['url']
		if db.item.find_one({'link':rss['link']}):
			continue
		rss['title'] = i['title']
		rss['des'] = i.get('description')
		rss['imgurl'] = i.get('titleImg')
		try:
			rss['pubdate'] = now() if not i.get('releaseDate') else \
				datetime.datetime.strptime(i.get('releaseDate'), '%Y-%m-%d %X')
			if checkRss(rss):
				rsslist.append(rss)
		except Exception, e:
			print e
	saveRsslist(rsslist, site)

def hustBBS(site):
	html = urllib2.urlopen(site['url']).read()
	soup = BeautifulSoup(html.decode('gbk'))
	rsslist = []
	for i in soup.find_all('post'):
		rss = {'source':site['source'], 'tags':[], 'category':site['category'], \
			'click_num':0, 'favo_num':0}
		rss['title'] = i.find('title').get_text()
		board = i.find('board').get_text()
		ifile = i.find('file').get_text()
		reply_count = i.find('reply_count').get_text()
		rss['link'] = 'http://bbs.whnet.edu.cn/cgi-bin/bbstcon?board='+board+'&file='+ifile
		rss['des'] = u'板块:'+board+u'   回复人数:'+reply_count
		rss['pubdate'] = now()
		if checkRss(rss):
			rsslist.append(rss)
	saveRsslist(rsslist, site)

def googlenews(site):
	rssraw = feedparser.parse(site['url'])
	rsslist = []
	for i in rssraw['entries']:
		rss = {'click_num':0, 'favo_num':0}
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
			if checkRss(rss):
				rsslist.append(rss)
		except Exception, e:
			print e
	saveRsslist(rsslist, site)

def pento(site):
	BASE_URL = 'http://www.pento.cn'
	html = urllib2.urlopen(site['url']).read()
	soup = BeautifulSoup(html)
	rsslist = []
	for i in soup.find_all(class_='book_list_box'):
		rss = {'source':site['source'], 'tags':[], 'category':site['category'], \
			'click_num':0, 'favo_num':0}
		titlea = i.find('div', class_='book_card_title').find('a')
		try :
			rss['title'] = titlea.get_text()
			rss['link'] = BASE_URL + titlea.get('href')
			rss['des'] = i.find('div', class_='book_card_content').get_text()
			pubdate = i.find('div', class_='book_card_time').get_text()
			rss['imgurl'] = i.find('input').get('value')
			rss['pubdate'] = datetime.datetime.strptime(pubdate, '%Y-%m-%d')
			if checkRss(rss):
				rsslist.append(rss)
		except :
			pass
	saveRsslist(rsslist, site)

def run():
	global db
	import pymongo
	conn_primary = pymongo.Connection(PARAMS['db_primary']['ip'])
	db = conn_primary['feed']
	db.authenticate(PARAMS['db_primary']['username'], PARAMS['db_primary']['password'])

	# sites.updatesites()
	for i in db.site.find({'active':True}, timeout=False):
		try:
			exec( i['parser']+'(i)' )
		except Exception, e:
			print i['url'] + str(e)
	conn_primary.close()

if __name__ == '__main__':
	pass