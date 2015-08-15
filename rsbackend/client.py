#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rsjm import *

def initRSJM():
#    updateUPre(interval=24*60*60)
#    updateRList(interval=3*60*60)
#    updateLsiDic(interval=5*24*60*60)
#    updateClassifyDic(interval=15*24*60*60)
    feed(interval=12*60*60)

if __name__ == '__main__':
	initRSJM()
