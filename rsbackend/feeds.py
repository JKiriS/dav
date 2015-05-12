#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import urllib2
from bs4 import BeautifulSoup
import feedparser
import datetime, time
import Queue
import json
import urlparse
import random
from xml.etree import ElementTree as ET
import os, sys
import threading

WORK_N = 5
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PARAMS_DIR = os.path.join(BASE_DIR,'self.cfg')
PARAMS = json.load(file(PARAMS_DIR))

import pymongo
conn_primary = pymongo.Connection(PARAMS['db_primary']['ip'])
db = conn_primary['feed']
db.authenticate(PARAMS['db_primary']['username'], PARAMS['db_primary']['password'])

socket.setdefaulttimeout(PARAMS['feed']['timeout'])
now = lambda : datetime.datetime.utcnow()

class RsslistNull(Exception):
    def __init__(self):
        self.code = 1001
        self.msg = 'Rsslist is empty'
    def __str__(self):
        return 'Error[' + repr(self.code) + ' ' + self.msg

class Parser:
    def __init__(self, site):
        self._site = site;
        self._rsslist = []
    def checkrss(self, rss):
        if 'des' not in rss or len(rss['des']) < 10:
            return False
        elif len(rss['des']) >= 500:
            rss['des'] = rss['des'][:500]+'...'
        rss['rand'] = [random.random(), 0]
        self._rsslist.append(rss)
    def save(self):
        if len(self._rsslist) > 0:
            db.item.insert(self._rsslist, continue_on_error=True)
            self._site['latest'] = self._rsslist[0]['pubdate']
            db.site.save(self._site)
        else :
            raise RsslistNull()

class common(Parser):
    def simplerss(self, rawitem, checktime=True):
        rss = {'click_num':0, 'favo_num':0}
        try:
            rss['pubdate'] = now() if rawitem.get('published_parsed') == None else \
                datetime.datetime.fromtimestamp( time.mktime(rawitem['published_parsed']) )
            if checktime:
                if self._site.get('latest') and rss['pubdate'] <= self._site['latest']:
                    return None
            rss['source'] = self._site['source']
            rss['tags'] = []
            rss['category'] = self._site['category']
            for t in rawitem.get('tags', []):
                if t.term not in rss['tags']:
                    rss['tags'].append(t.term)
            rss['title'] = rawitem['title']
            rss['link'] = rawitem['link']
        except Exception, e:
            print e
            return None
        return rss
    def getdesimg(self, rss, rawtext):
        if 'summary_detail' in rawtext:
            des = rawtext['summary_detail']['value']
            soup = BeautifulSoup(des)
            rss['des'] = soup.get_text()
    def parse(self):
        rawrss = feedparser.parse(self._site['url'])
        for i in rawrss['entries']:
            rss = self.simplerss(i)
            if rss is None:
                continue
            self.getdesimg(rss, i)
            self.checkrss(rss)
        self.save()

class imgInEnclosure(common):
    def getdesimg(self, rss, rawtext):
        if rss != None and 'summary_detail' in rawtext:
            des = rawtext['summary_detail']['value']
            soup = BeautifulSoup(des)
            rss['des'] = soup.get_text()
        if rss != None and len(rawtext.enclosures) > 0 and \
                        rawtext.enclosures[0]['type'] == 'image/jpeg' :
            rss['imgurl'] = rawtext.enclosures[0]['href']

class imgInDes(common):
    def getdesimg(self, rss, rawtext):
        if rss != None and 'summary_detail' in rawtext:
            des = rawtext['summary_detail']['value']
            soup = BeautifulSoup(des)
            rss['des'] = soup.get_text()
            if soup.find('img'):
                rss['imgurl'] = soup.find('img').get('src')

class imgInContent(common):
    def getdesimg(self, rss, rawtext):
        if rss != None and 'summary_detail' in rawtext:
            des = rawtext['summary_detail']['value']
            soup = BeautifulSoup(des)
            rss['des'] = soup.get_text()
            if 'content' in rawtext:
                soup = BeautifulSoup(rawtext.content[0].value)
                if soup.find('img'):
                    rss['imgurl'] = soup.find('img').get('src')

class desImgInContent(common):
    def getdesimg(self, rss, rawtext):
        if rss != None and 'content' in rawtext:
            content = reduce(lambda a,b:a+b.value, rawtext.content, '')
            soup = BeautifulSoup(content)
            rss['des'] = soup.get_text()
            if soup.find('img'):
                rss['imgurl'] = soup.find('img').get('src')

class ifanr(Parser):
    def parse(self):
        rawrss = urllib2.urlopen(self._site['url'])
        channel = ET.parse(rawrss).find('./channel')
        for i in channel.findall('item'):
            rss = {'click_num':0, 'favo_num':0}
            rss['pubdate'] = datetime.datetime.strptime(i.find('pubDate').text[:-6], '%a, %d %b %Y %X')
            if self._site.get('latest') and rss['pubdate'] <= self._site['latest']:
                break
            rss['source'] = self._site['source']
            rss['tags'] = []
            rss['category'] = self._site['category']
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
            self.checkrss(rss)
        self.save()

class acfun(Parser):
    def parse(self):
        baseurl = 'http://www.acfun.tv'
        data = urllib2.urlopen(self._site['url']).read()
        for i in json.loads(data):
            rss = {'source':self._site['source'], 'tags':[], 'category':self._site['category'], \
                   'click_num':0, 'favo_num':0}
            rss['link'] = baseurl + i['url']
            rss['title'] = i['title']
            rss['des'] = i.get('description')
            rss['imgurl'] = i.get('titleImg')
            try:
                rss['pubdate'] = now() if not i.get('releaseDate') else \
                    datetime.datetime.strptime(i.get('releaseDate'), '%Y-%m-%d %X')
                self.checkrss(rss)
            except Exception, e:
                print e
        self.save()

class hustBBS(Parser):
    def parse(self):
        html = urllib2.urlopen(self._site['url']).read()
        soup = BeautifulSoup(html.decode('gbk'))
        for i in soup.find_all('post'):
            rss = {'source':self._site['source'], 'tags':[], 'category':self._site['category'], \
                   'click_num':0, 'favo_num':0}
            rss['title'] = i.find('title').get_text()
            board = i.find('board').get_text()
            ifile = i.find('file').get_text()
            reply_count = i.find('reply_count').get_text()
            rss['link'] = 'http://bbs.whnet.edu.cn/cgi-bin/bbstcon?board='+board+'&file='+ifile
            rss['des'] = u'板块:'+board+u'   回复人数:'+reply_count
            rss['pubdate'] = now()
            self.checkrss(rss)
        self.save()

class googlenews(common):
    def parse(self):
        rssraw = feedparser.parse(self._site['url'])
        for i in rssraw['entries']:
            rss = self.simplerss(i, False)
            self.getdesimg(rss, i)
            link = urlparse.urlparse( i['link'] )
            rss['link'] = urlparse.parse_qs(link.query, True).get('url')[0]
            self.checkrss(rss)
        self.save()

class pento(Parser):
    def parse(self):
        BASE_URL = 'http://www.pento.cn'
        html = urllib2.urlopen(self._site['url']).read()
        soup = BeautifulSoup(html)
        rsslist = []
        for i in soup.find_all(class_='book_list_box'):
            rss = {'source':self._site['source'], 'tags':[], 'category':self._site['category'], \
                   'click_num':0, 'favo_num':0}
            titlea = i.find('div', class_='book_card_title').find('a')
            try :
                rss['title'] = titlea.get_text()
                rss['link'] = BASE_URL + titlea.get('href')
                rss['des'] = i.find('div', class_='book_card_content').get_text()
                pubdate = i.find('div', class_='book_card_time').get_text()
                rss['imgurl'] = i.find('input').get('value')
                rss['pubdate'] = datetime.datetime.strptime(pubdate, '%Y-%m-%d')
                self.checkRss(rss)
            except :
                pass
        self.save()
'''
site status: enabled running error disabled
'''
def worker(q, db):
    while True:
        i = q.get()
        try:
            db.site.update({'_id':i['_id']}, {'$set':{'status':'running'}})
            exec( i['parser']+'(i).parse()' )
            db.site.update({'_id':i['_id']}, {'$set':{'status':'enabled'}})
        except Exception, e:
            db.site.update({'_id':i['_id']}, {'$set':{'status':'error'}})
            print i['url'] + str(e)
        finally:
            q.task_done()

def run():
    q = Queue.JoinableQueue()
    for i in range(WORK_N):
        t = threading.Thread(target=worker, args=(q, db))
        t.daemon = True
        t.start()
    for i in db.site.find({'status':{'$ne':'disabled'}}, timeout=False):
        q.put(i)
    q.join()

if __name__ == '__main__':
    run()