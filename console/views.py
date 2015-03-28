#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from console.models import site, job
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context
from django.template.loader import get_template
from mongoengine import Q
import datetime, time
from bson import ObjectId
from dav import settings
import os.path
import random
import urllib2

# Create your views here.
now = lambda : datetime.datetime.now()

def rsconsole(request):
	if not request.user.is_superuser:
		return HttpResponseRedirect('/account/login?redirecturl=/console/rs')
	return render(request, 'rs_console.html', locals())


gservices = [
			{'id':'ClsService','name':'classify','domain':'rs','status':'running'},
			{'id':'RecService','name':'recommend','domain':'rs','status':'running'},
			{'id':'SearchService','name':'search','domain':'rs','status':'running'},
			{'id':'DBSync','name':'DBSync','domain':'main','status':'closed'},
			{'id':'JobManager','name':'JobManager','domain':'main','status':'running'},
		]
def getservices(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {}
		services = gservices
		t = get_template('services.html')
		c = Context(locals())
		res['data'] = t.render(c)
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

def findservice(target):
	for s in gservices:
		if s['id'] == target:
			return s
	return Exception()


def setservices(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		target = request.POST['target']
		cmd = request.POST['cmd']
		res = {}
		try:
			s = findservice(target)
			if cmd == u'关闭':
				s['status'] = 'closed'
			else:
				s['status'] = 'running'
			tem =  Template('''
				<td>{{ s.name }}</td>
				<td>{{ s.domain }}</td>
	  			<td class="status">
					<span class="status-label">{{ s.status }}</span>
					<button type="button" class="btn btn-primary btn-sm">{% ifequal s.status 'running' %}关闭{% else %}开启{% endifequal %}</button>
				</td>
			''')
			c = Context(locals())
			res['data'] = tem.render(c)
		except Exception, e:
			print e
			res['error'] = u'无法' + cmd + target
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

def getsites(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {}
		sites = site.objects()
		t = get_template('sites.html')
		c = Context(locals())
		res['data'] = t.render(c)
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

def setsites(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		target = request.POST['target']
		cmd = request.POST['cmd']
		res = {}
		try:
			s = site.objects(id=ObjectId(target)).first()
			if cmd == u'禁用':
				s['status'] = 'disabled'
			else:
				s['status'] = 'enabled'
			s.save()
			tem =  Template('''
				<td><span title="{{ s.url }}">{{ s.url |slice:"30" }}</span></td>
		  		<td>{{ s.parser }}</td>
		  		<td>{{ s.category }}</td>
		  		<td>{{ s.source }}</td>
		  		<td>{{ s.latest|date:"Y-m-d H:i:s" }}</td>
		  		<td class="status">
		  			<span class="status-label">{{ s.status }}</span>
		  			<button type="button" class="btn btn-primary btn-sm">{% ifequal s.status 'enabled' %}禁用{% else %}启用{% endifequal %}</button>
		  		</td>
			''')
			c = Context(locals())
			res['data'] = tem.render(c)
		except Exception, e:
			print e
			res['error'] = u'无法' + cmd + ' site:' + target
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

def getjobs(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {}
		jobs = job.objects().order_by("-starttime")
		t = get_template('jobs.html')
		c = Context(locals())
		res['data'] = t.render(c)
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

def setjobs(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		target = request.POST['target']
		cmd = request.POST['cmd']
		res = {}
		try:
			j = job.objects(id=ObjectId(target)).first()
			if cmd == u'取消':
				j['status'] = 'canceled'
			elif cmd == u'修改':
				j['starttime'] = request.POST['arg']
			elif cmd == u'激活':
				j['status'] = 'waiting'
			j.save()
			tem =  Template('''
				<td>{{ j.function }}</td>
      			<td>{{ j.status }}</td>
		      	<td>{{ j.starttime|date:"Y-m-d H:i:s" }}</td>
		      	<td>
		        	{% ifequal j.status 'waiting' %}
			        <button class="btn btn-primary btn-sm" disabled="disabled">修改</button>
			        <button class="btn btn-primary btn-sm">取消</button>
			        {% else %}
			           {% ifequal j.status 'canceled' %}
			            <button class="btn btn-primary btn-sm">激活</button>
			            {% endifequal %}
			        {% endifequal %}
		      	</td>
			''')
			c = Context(locals())
			res['data'] = tem.render(c)
		except Exception, e:
			print e
			res['error'] = u'无法' + cmd + ' job:' + target
		response.write( json.dumps(res, ensure_ascii=False) )
		return response