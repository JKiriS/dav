#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2
import json

params = json.load(file('../self.cfg'))
def run():
	url = 'http://127.0.0.1:8899/updateindex?pw=' + params['search_password']
	try:
		urllib2.urlopen(url).read()
	except :
		print 'SearchServer not available'

if __name__ == '__main__':
	pass

