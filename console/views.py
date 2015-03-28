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
import re
import commands

PARAMS_DIR = os.path.join(settings.BASE_DIR, 'self.cfg')
PARAMS = json.load(file(PARAMS_DIR))

# Create your views here.
now = lambda : datetime.datetime.now()

class ServiceManager:
	def __init__(self):
		self._services = {}
		self._data = [
			{'id':'ClsService','name':'classify','domain':'rs','status':'running'},
			{'id':'RecService','name':'recommend','domain':'rs','status':'running'},
			{'id':'SearchService','name':'search','domain':'rs','status':'running'},
			{'id':'DBSync','name':'DBSync','domain':'main','status':'running'},
			{'id':'JobManager','name':'JobManager','domain':'main','status':'running'},
		]
		for i, s in enumerate(self._data):
			self._services[s['id']] = i

	def _getstatusbycmd(self, sid, cmd):
		try:
			output = commands.getoutput(cmd)
			if output == '':
				raise Exception()
			for i in output.split('\n'):
				print i
				if not re.search(r'grep', i):					
					self._data[self._services[sid]]['status'] = 'running'
					return
			self._data[self._services[sid]]['status'] = 'closed'
		except:
			self._data[self._services[sid]]['status'] = 'closed'
	def getstatus(self):
		from thrift.transport import TSocket
		#test ClsService
		try: 
			transport = TSocket.TSocket(PARAMS['classify']['ip'],PARAMS['classify']['port'])
			transport.open()
			transport.close()
		except :
			self._data[self._services['ClsService']]['status']  = 'closed'
		# test RecService
		try:
			transport = TSocket.TSocket(PARAMS['recommend']['ip'],PARAMS['recommend']['port'])
			transport.open()
			transport.close()
		except :
			self._data[self._services['RecService']]['status'] = 'closed'
		# test SearchService
		try:
			transport = TSocket.TSocket(PARAMS['search']['ip'],PARAMS['search']['port'])
			transport.open()
			transport.close()
		except :
			self._data[self._services['SearchService']]['status']  = 'closed'
		# test DBSync
		self._getstatusbycmd('DBSync', 'ps aux|grep mongosync')
		self._getstatusbycmd('JobManager', 'ps aux|grep jobmanager.py')

	def getservices(self):
		self.getstatus()
		return self._data

	def getservice(self, sid):
		return self._data[self._services[sid]]

	def open(self, sid):
		if sid == 'DBSync':
			if self._data[self._services[sid]]['status'] == 'closed' and \
				commands.getstatusoutput("cd ~ && ./startdbsync.sh")[0] == 0:
				self._data[self._services[sid]]['status'] = 'running'
		elif sid == 'JobManager':
			if self._data[self._services[sid]]['status'] == 'closed' and \
				commands.getstatusoutput("cd ~/dav/rsbackend && nohup python jobmanager.py &")[0] == 0:
				self._data[self._services[sid]]['status'] = 'running'
		else:
			raise Exception()

	def close(self, sid):
		if sid == 'DBSync':
			if self._data[self._services[sid]]['status'] == 'running' and \
				commands.getstatusoutput("kill -9 $(ps -A|awk '/mongosync/{print $1}')")[0] == 0:
				self._data[self._services[sid]]['status'] = 'closed'
		elif sid == 'JobManager':
			if self._data[self._services[sid]]['status'] == 'running' and \
				commands.getstatusoutput("kill -9 $(ps -A|awk '/jobmanager/{print $1}')")[0] == 0:
				self._data[self._services[sid]]['status'] = 'closed'
		else:
			raise Exception()

sm = ServiceManager()

def rsconsole(request):
	if not request.user.is_superuser:
		return HttpResponseRedirect('/account/login?redirecturl=/console/rs')
	return render(request, 'rs_console.html', locals())

def getservices(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {}
		services = sm.getservices()
		t = get_template('services.html')
		c = Context(locals())
		res['data'] = t.render(c)
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

def setservices(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		target = request.POST['target']
		cmd = request.POST['cmd']
		res = {}
		try:
			if cmd == u'关闭':
				sm.close(target)
			else:
				sm.open(target)
			s = sm.getservice(target)
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