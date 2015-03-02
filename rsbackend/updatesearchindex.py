#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2

def run():
	url = 'http://127.0.0.1:8899/updateindex?pw=910813gyb'
	try:
		urllib2.urlopen(url).read()
	except :
		print 'SearchServer not available'

if __name__ == '__main__':
	pass

