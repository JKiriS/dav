# -*- coding: utf-8 -*-

import pymongo
import time, datetime
import feeds
import recommend
import calcupre
import updateindex

if __name__ == '__main__':
	while True:
		conn = pymongo.Connection()
		db = conn['feed']
		db.authenticate('JKiriS','910813gyb')
		for j in db.job.find({'starttime':{'$lt':datetime.datetime.now()}}, timeout=False):
			try:
				exec('reload(' + j['module'] + ')')
				exec( j['module'] + '.run()' )
				db.job.remove({'_id':j['_id']})
			except Exception, e:
				print j['module'] + str(e)
		conn.close()
		time.sleep(60 * 15)