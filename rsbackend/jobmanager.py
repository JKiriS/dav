# -*- coding: utf-8 -*-

import pymongo
import time, datetime
import feeds
import recommend
import calcupre
import json
import updatesearchindex

params = json.load(file('../self.cfg'))

if __name__ == '__main__':
	while True:
		conn = pymongo.Connection()
		db = conn['feed']
		db.authenticate(params['db_username'], params['db_password'])
		for j in db.job.find({'starttime':{'$lt':datetime.datetime.now()}, \
				'status':'waiting'}, timeout=False):
			try:
				db.job.update({'_id':j['_id']}, {'$set':{'status':'running'}})
				exec('reload(' + j['module'] + ')')
				exec( j['module'] + '.run()' )
				db.job.remove({'_id':j['_id']})
			except Exception, e:
				db.job.update({'_id':j['_id']}, {'$set':{'status':'failed'}})
				print j['module'] + str(e)
		conn.close()
		time.sleep(60 * 15)