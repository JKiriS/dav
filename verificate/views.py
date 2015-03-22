#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from verificate.models import verification, mousetrail
import random
import json
from bson import ObjectId
from django.template import Template, Context
from django.http import HttpResponse, HttpResponseRedirect
import re
from django.template.loader import get_template
# Create your views here.

def getquestion(request): 
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	v = verification.objects(rand__near=[random.random(), 0]).first()
	res = {}
	if v:
		tem = get_template("veri_q_s.html")
		c = Context(locals())
		res['data'] = tem.render(c)
	response.write( json.dumps(res, ensure_ascii=False) )
	return response

def collectselect(request):
	if request.method == 'POST':
		v = verification.objects(id=request.POST['qid']).first()
		if v:
			try:
				v.selection.append(int(request.POST['select']))
				v.save()
			except:
				pass
	return HttpResponse()

def collectmousetrail(request):
	traildata = request.POST.getlist('data[]', [])
	if 'click' in traildata:
		m = mousetrail(uid=request.user.id, traildata=traildata, useragent=request.META['HTTP_USER_AGENT'])
		m.save()
	return HttpResponse()