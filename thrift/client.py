#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('./gen-py')
 
from recsys import RecSys
 
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
 
try:
	transport = TSocket.TSocket('115.156.196.215', 9090)
	transport = TTransport.TBufferedTransport(transport)
	protocol = TBinaryProtocol.TBinaryProtocol(transport)
	client = RecSys.Client(protocol)
	transport.open()
 
	print 'start'
	print client.updateRList('5459d5ee7c46d50ae022b901')
	# print client.updateUPre('5459d5ee7c46d50ae022b901')
	# print client.updateLsiIndex('文化')
	# print client.updateLsiDic('文化')
	# print client.trainClassify()
	# print client.classify('文化')

	transport.close()
 
except Thrift.TException, ex:
	print "%s" % (ex.message)