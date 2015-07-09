#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from topicmsg.models import topic, material, message
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context
from django.template.loader import get_template
from mongoengine import Q
import datetime, time
from bson import ObjectId
from dav import settings
from dav.baseclasses import PostResponse
import os.path, sys
import random
from markdown import markdown  
 

# Create your views here.
now = lambda : datetime.datetime.utcnow()

def topicindex(request):
	t = topic.objects(id=ObjectId(request.GET['id'])).first()
	return render(request, 'topicmsg_main.html', locals())

def getmsgdetail(request):
	if request.method == 'POST':
		response = PostResponse()
		target = request.POST['id']
		msg = message.objects(id=ObjectId(target)).first()
		if msg:
			response.render(get_template('msgdetail.html'), locals())
		else:
			response.seterror("msg not exist")
		return response.get()

def topiclist(request):
	return render(request, 'topiclist.html', locals())

def newtopicmodal(request):
	# if not request.user.is_authenticated():
	# 	return HttpResponseRedirect('/account/login?redirecturl=/topicmsg/topiclist')
	if request.method == 'POST':
		response = PostResponse(request.POST)
		response.render(get_template('newtopicmodal.html'), {})
		return response.get()

def createtopic(request):
	if request.method == 'POST':
		response = PostResponse()
		title = request.POST['title']
		t = topic(title=title)
		t.save()
		response.setparams('redirecturl', '/topicmsg/topic?id='+str(t.id))
		return response.get()

def getmateriallist(request):
	if request.method == 'POST':
		response = PostResponse()
		t = topic.objects(id=ObjectId(request.POST['topic'])).first()
		if t:
			orders = t.materials[::-1]
			materiallist = material.objects(id__in=orders)
			tem =  Template('''
				{% load newlibrary %}
				{% reorder materiallist by orders as materiallist %}
				{% for m in materiallist%}
					<a href="{{ m.url }}" class="material" id="{{ m.id }}">{{ m.title }}</a>
				{% endfor %}
				''')
			response.render(tem, locals())
		else:
			response.seterror('topic not exist')
		return response.get()

def addmaterial(request):
	if request.method == 'POST':
		response = PostResponse()
		target = request.POST['topic']
		url = request.POST['url']
		title = request.POST['title']
		m = material(url=url, title=title)
		t = topic.objects(id=ObjectId(target)).first()
		if t:
			m.save()
			t.materials.append(m.id)
			t.save()
			tem =  Template('''
				<a href="{{ m.url }}" class="material" id="{{ m.id }}">{{ m.title }}</a>
				''')
			response.render(tem, locals())
			msg = message(topic=t.id,title=u'添加了新资料',timestamp=now(),
				content=u'<a href="{}" id="{}">{}</a>'.format(m.url,m.id,m.title),
				user={'id':request.user.id,'name':request.user.username})
			msg.save()
		else:
			response.seterror('topic not exist')
		return response.get()

def addmsg(request):
	if request.method == 'POST':
		response = PostResponse()
		target = request.POST['topic']
		content = request.POST['content']
		title = request.POST['title']
		msg = message(topic=ObjectId(target),title=title,timestamp=now(),content=markdown(content), \
			user={'id':request.user.id,'name':request.user.username})
		msg.save()		
		return response.get()

import threading, time
class Timer(threading.Thread):
	def __init__(self, sleep=80):
		threading.Thread.__init__(self)
		self.sleep = sleep
		self.setDaemon(True)
		self.status = 'running'     
	def run(self):
		while self.status == 'running':
			time.sleep(self.sleep)
			self.status = 'timeout'   
	def stop(self):
		self.status = 'stoped'

def getmsglist(request):
	if request.method == 'POST':
		response = PostResponse()
		target = request.POST['topic']
		lastmsgid = request.POST['lastmsgid']
		t = Timer(int(request.POST['time']))
		dtoffset = datetime.timedelta(minutes=int(request.POST['dtoffset']))
		if lastmsgid == '':
			msglist = message.objects(topic=ObjectId(target))	
		else:
			t.start()
			while t.status == 'running':
				msglist = message.objects(topic=ObjectId(target),id__gt=ObjectId(lastmsgid))
				if len(msglist) > 0:
					t.stop()
					break
				time.sleep(0.5)
		if lastmsgid == '' or t.status == 'stoped':
			response.render(get_template('msglist.html'), locals())
		elif t.status == 'timeout':
			response.seterror('timeout')
		return response.get()