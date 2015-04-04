#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from rs.models import item, behavior, site, rlist, upre, category, source, searchresult
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
 
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# Create your views here.

PARAMS_DIR = os.path.join(settings.BASE_DIR, 'self.cfg')
PARAMS = json.load(file(PARAMS_DIR))

sys.path.append(PARAMS['thrift']['gen-py'])
from search import Search
from common import *

now = lambda : datetime.datetime.utcnow()

def index(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect('/rs/recommend')
	else :
		return HttpResponseRedirect('/rs/lookaround')

def lookaround(request):
	col = 'lookaround'
	if request.method == 'POST':
		response = PostResponse(request.POST)
		itemlist = item.objects(pubdate__gte=now()-datetime.timedelta(days=5), \
			rand__near=[random.random(), 0]).limit(15)
		dtoffset = datetime.timedelta(minutes=int(request.POST['dtoffset']))
		hasmore = True if len(itemlist) >= 15 else False
		response.render(get_template('rs_itemlist.html'), locals())
		response.setparams('start', 0)
		return response.get()
	
	return render(request, 'rs_main.html', locals())

def recommend(request):
	col = 'recommend'
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/account/login?redirecturl=/rs/recommend')
	if request.method == 'POST':
		response = PostResponse(request.POST)
		skipnum = int(request.POST['start'])
		urlist = rlist.objects(id=request.user.id).first()
		itemlist = item.objects(id__in=urlist.rlist[skipnum:skipnum+15])
		dtoffset = datetime.timedelta(minutes=int(request.POST['dtoffset']))
		orders = urlist.rlist[skipnum:skipnum+15]
		hasmore = True if len(orders) >= 15 else False
		response.render(get_template('rs_itemlist.html'), locals())
		response.setparams('start', repr(skipnum + len(itemlist)))
		return response.get()

	return render(request, 'rs_main.html', locals())

def lookclassify(request):
	col = 'lookclassify'
	param_c = request.GET.getlist('category[]',[])
	param_s = request.GET.getlist('source[]',[])
	if request.method == 'POST':
		response = PostResponse(request.POST)
		skipnum = int(request.POST['start'])
		orderby = request.GET.get('orderby', 'time')
		dtoffset = datetime.timedelta(minutes=int(request.POST['dtoffset']))
		if orderby == 'time':
			itemlist = item.objects( Q(source__in=param_s) | Q(category__in=param_c) )\
				.order_by("-pubdate").skip(skipnum).limit(15)
		elif orderby == 'hot':
			itemlist = item.objects( Q(source__in=param_s) | Q(category__in=param_c) )\
				.order_by("-click_num").skip(skipnum).limit(15)
		elif orderby == 'favo':
			itemlist = item.objects( Q(source__in=param_s) | Q(category__in=param_c) )\
				.order_by("-favo_num").skip(skipnum).limit(15)
		else:
			itemlist = item.objects( (Q(source__in=param_s) | Q(category__in=param_c)) & \
				Q(pubdate__gte=now()-datetime.timedelta(days=10)) & \
				Q(rand__near=[random.random(), 0]) ).limit(15)
		hasmore = True if len(itemlist) >= 15 else False
		if orderby == 'random':
			response.setparams('start', 0)
		else:
			response.setparams('start', repr(skipnum + len(itemlist)))
		response.render(get_template('rs_itemlist.html'), locals())
		return response.get()
	if len(param_c) + len(param_s) > 0:
		for c in param_c:
			category.objects(name=c).update(inc__visit_num=1) 
			b = behavior(uid=request.user.id, action='visitcategory', \
				target=c, timestamp=now())
			b.save()
		for s in param_s:
			source.objects(name=s).update(inc__visit_num=1)
			b = behavior(uid=request.user.id, action='visitsource', \
				target=s, timestamp=now())
			b.save()
		classname = u'和'.join([u'、'.join(param_c), u'、'.join(param_s)])
		if classname.startswith(u'和'):
			classname = classname[1:]
		if classname.endswith(u'和'):
			classname = classname[:-1]
		return render(request, 'rs_main.html', locals())
	else :
		return HttpResponseRedirect('/rs/lookaround')

def getcs(request):
	if request.method == 'POST':
		response = PostResponse()
		_url = request.POST.get('fromurl').split('?')
		from django.http import QueryDict
		try:
			qd = QueryDict(_url[1].encode('utf-8'))
			param_c = qd.getlist('category[]',[])
			param_s = qd.getlist('source[]',[])
			orderby = qd.get('orderby','time')
		except:
			param_c, param_s = [], []
			orderby = 'time'
		submitdisabled = False if len(param_c) + len(param_s) > 0 else True
		pre = None;
		if request.user.id:
			pre = upre.objects(id=request.user.id).first()
		if pre:
			sources = map(lambda a:a[0], \
				sorted(pre.source.iteritems(), key=lambda a:a[1], reverse=True))
			categories = map(lambda a:a[0], \
				sorted(pre.category.iteritems(), key=lambda a:a[1], reverse=True))
		else:
			sources = map(lambda a:a['name'], source.objects().order_by("-visit_num"))
			categories = map(lambda a:a['name'], category.objects().order_by("-visit_num"))
		sources_show = sources[:10]
		sources_hide = sources[10:]
		has_hide = True if len(sources_hide) > 0 else False
		response.render(get_template('rs_category_source.html'), locals())
		return response.get()
		return response

def search(request):
	col = 'search'
	if request.method == 'POST':
		b = behavior(uid=request.user.id, action='search', \
			target=request.GET['wd'], timestamp=now())
		b.save()
		response = PostResponse(request.POST)
		start = int(request.POST['start'])
		dtoffset = datetime.timedelta(minutes=int(request.POST['dtoffset']))
		if start == 0:
			sid = ObjectId()
			response.setparams('searchid', str(sid))
			s = searchresult(id=sid,wd=request.GET['wd'],timestamp=now())
			s.save()
		try:
			transport = TSocket.TSocket(PARAMS['search']['ip'],PARAMS['search']['port'])
			transport = TTransport.TBufferedTransport(transport)
			protocol = TBinaryProtocol.TBinaryProtocol(transport)
			client = Search.Client(protocol)
			transport.open()
			sresult = client.search(request.GET['wd'].encode('utf-8'), start, 15)
			transport.close()
			
			slist = eval(sresult.data['searchresult']) if sresult.data else []
			hasmore = eval(sresult.data['hasmore']) if sresult.data else False 
			itemlist = item.objects(id__in=slist)
			orders = slist
			wd = request.GET['wd']
			response.render(get_template('rs_itemlist.html'), locals())
			response.setparams('start', repr(start + len(itemlist)))
		except Exception, e:
			response.seterror(str(e))
		return response.get()
	if 'wd' in request.GET:
		wd = request.GET['wd']
		return render(request, 'rs_main.html', locals())
	else :
		return HttpResponseRedirect('/rs/lookaround')

def selffavorites(request):
	col = 'selffavorites'
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/account/login?redirecturl=/rs/selffavorites')
	if request.method == 'POST' and request.user.is_authenticated():
		response = PostResponse(request.POST)
		skipnum = int(request.POST['start'])
		dtoffset = datetime.timedelta(minutes=int(request.POST['dtoffset']))
		if skipnum == 0:
			itemlist = item.objects(id__in=request.user.favorites[-15-skipnum:])
			orders = request.user.favorites[-15-skipnum:][::-1]
		else :
			itemlist = item.objects(id__in=request.user.favorites[-15-skipnum:-skipnum])
			orders = request.user.favorites[-15-skipnum:-skipnum][::-1]

		hasmore = True if len(itemlist) >= 15 else False
		response.render(get_template('rs_itemlist.html'), locals())
		response.setparams('start', repr(skipnum + len(itemlist)))
		return response.get()

	return render(request, 'rs_main.html', locals())

def selfpre(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/account/login?redirecturl=/rs/selfpre')
	return render(request, 'rs_selfpre.html', locals())

def behaviorrecorder(request):
	if request.method == 'POST': 
		item.objects(id=ObjectId(request.POST['target'])).update(inc__click_num=1)
		b = behavior(uid=request.user.id, action='clickitem',\
			target=request.POST['target'], timestamp=now(), 
			fromurl=request.POST['fromurl'])
		b.save()
		if 'searchid' in request.POST:
			sr = searchresult.objects(id=request.POST['searchid']).first()
			sr.click.append( ObjectId(request.POST['target']) )
			sr.save()
	return HttpResponse()

def additemtag(request):
	if request.method == 'POST':
		response = PostResponse()
		i = item.objects(id=request.POST['itemid']).first()
		b = behavior(uid=request.user.id,action='addtag',\
			target=request.POST['itemid'],timestamp=now())
		b.save()
		if request.POST['name'] not in i.tags:
			i.tags.append(request.POST['name'])
			i.save()
			tem = Template('''<a class="itemtag" target="_blank" 
				href="{% url 'lookclassified' %}?tag={{ t }}">#{{ t }}</span></a>''')
			response.render(tem, {'t': request.POST['name']})
		return response.get()

def getupre(request):
	response = PostResponse()
	pre = upre.objects(id=request.user.id).first()
	if pre:
		if request.GET['target'] == 'source' and pre.source :
			response.setdata(map(lambda a:{'name':a[0],'count':a[1]}, \
				sorted(pre.source.iteritems(), key=lambda a:a[1], reverse=True))[:30])
		if request.GET['target'] == 'category' and pre.category :
			response.setdata(map(lambda a:{'name':a[0],'count':a[1]}, \
				sorted(pre.category.iteritems(), key=lambda a:a[1], reverse=True))[:30])
		if request.GET['target'] == 'wd' and pre.wd:
			response.setdata(map(lambda a:{'name':a[0],'count':a[1]}, \
				sorted(pre.wd.iteritems(), key=lambda a:a[1], reverse=True))[:100])
	return response.get()

def addfavorite(request):
	if request.method == 'POST':
		item.objects(id=request.POST['target']).update(inc__favo_num=1)
		if request.user.is_authenticated():
			target = request.POST.get('target')
			request.user.favorites.append( ObjectId(target) )
			request.user.save()
		b = behavior(uid=request.user.id, action='addfavorite',\
			target=request.POST['target'], timestamp=now())
		b.save()
	return HttpResponse()

def removefavorite(request):
	if request.user.is_authenticated():
		target = request.POST.get('target')
		request.user.favorites.remove( ObjectId(target) )
		request.user.save()
		b = behavior(uid=request.user.id, action='rmfavorite',\
			target=request.POST['target'], timestamp=now())
		b.save()
	return HttpResponse()