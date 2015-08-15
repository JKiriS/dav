#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('./gen-py')
 
from search import Search
from rec import Rec
from cls import Cls
from common import *

from bson import ObjectId
 
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

def test_rec(host='115.156.197.96', port=9090):
	transport = TSocket.TSocket(host, port)
	transport = TTransport.TBufferedTransport(transport)
	protocol = TBinaryProtocol.TBinaryProtocol(transport)
	client = Rec.Client(protocol)
	transport.open()

	print 'start'
	# print client.updateTfIdf(30000)
	# for i in range(40):
	# 	print i
	# 	print client.updateModel(3000, 100)
	# print client.lsiSearch('微信', 0, 15)
	print client.updateRList('5459d5ee7c46d50ae022b901')

	transport.close()

if __name__ == '__main__':
	test_rec()