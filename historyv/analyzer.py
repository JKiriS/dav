# -*- coding: utf-8 -*-

import sqlite3
import json
from urlparse import urlsplit
import tldextract

cx = sqlite3.connect('History')
cu = cx.cursor()
cu.execute('select url,visit_count from urls order by visit_count desc limit 1000')
urls_dict = {}
for i in cu.fetchall():
	ext = tldextract.extract(i[0])
	domain = ext.domain
	subdomain = ext.subdomain
	if domain == '':
		continue
	sd = subdomain+'.'+domain
	if urls_dict.has_key(domain):
		if urls_dict[domain].has_key(sd):
			urls_dict[domain][sd] += i[1]+1
		else :
			urls_dict[domain][sd] = i[1]
	else:
		urls_dict[domain] = {sd:i[1]}
cu.close()
cx.close()

urls = []
for k in urls_dict.keys():
	children = []
	sum = 0
	for ck in  urls_dict[k].keys():
		children.append({'name':ck,'size':urls_dict[k][ck]})
		sum += urls_dict[k][ck]
	children.sort(key=lambda a:a['size'], reverse=True)
	urls.append({'name':k, 'children':children, 'size':sum})
urls.sort(key=lambda a:a['name'], reverse=True)
json.dump({'name':'history','children':urls}, open('history.json','w'))

