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
 

transport = TSocket.TSocket('localhost', 9092)
transport = TTransport.TBufferedTransport(transport)
protocol = TBinaryProtocol.TBinaryProtocol(transport)
# client = Cls.Client(protocol)
client = Search.Client(protocol)
transport.open()

print 'start'
# print client.updateRList('5459d5ee7c46d50ae022b901')
# print client.updateUPre('5459d5ee7c46d50ae022b901')
# print client.updateLsiIndex('文化')
# print client.updateLsiDic('文化')
# print client.trainClassify()
# print client.classify('综合')
sid = ObjectId()
print sid
sresult = client.search(u"java", 0, 15)
searchresult = eval(sresult.data['searchresult'])
hasmore = eval(sresult.data['hasmore'])
print hasmore, searchreult
# print client.updateSearchIndex()

transport.close()