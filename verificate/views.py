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
# Create your views here.

def getquestion(request): 
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	v = verification.objects(rand__near=[random.random(), 0]).first()
	res = {}
	if v:
		tem = Template(
			u'''
			<div class="question" id="{{ v.id }}">
				<span>{{ v.question|safe }}</span>
			</div>
			<div class="option">
			{% for o in v.option %}
			<a href="javascript:void(0)" type="radio" class="robot-checker" value="{{ forloop.counter0 }}">
				<span class="glyphicon glyphicon-certificate" aria-hidden="true"></span>
			</a>
			<span class="robot-checker-des">{{ o }}</span>
			{% endfor %}
			</div>
			''')
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
	ismobile = False
	if re.match(r'iphone|ios|android|mini|mobile|mobi|Nokia|Symbian|iPod|iPad|Windows\s+Phone|MQQBrowser|wp7|wp8|UCBrowser7|UCWEB|360\s+Aphone\s+Browser', request.META['HTTP_USER_AGENT']):
		ismobile = True
	print ismobile
	if (not ismobile) and 'click' in traildata:
		m = mousetrail(uid=request.user.id, traildata=traildata)
		m.save()
	return HttpResponse()