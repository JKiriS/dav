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
import pymongo
from bson import ObjectId
from dav import settings
import os.path
import random
import urllib2

# Create your views here.
now = lambda : datetime.datetime.now()

def index(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect('/rs/recommend')
	else :
		return HttpResponseRedirect('/rs/lookaround')

def lookaround(request):
	col = 'lookaround'
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		itemlist = item.objects(pubdate__gte=now()-datetime.timedelta(days=5), \
			rand__near=[random.random(), 0]).limit(15)
		hasmore = True if len(itemlist) >= 15 else False
		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res = {}
		res['data'] = t.render(c)
		res['params'] = request.POST.copy()
		res['params']['start'] = 0
		response.write( json.dumps(res, ensure_ascii=False) )
		return response
	
	return render(request, 'rs_main.html', locals())

def recommend(request):
	col = 'recommend'
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/account/login?redirecturl=/rs/recommend')
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		skipnum = int(request.POST['start'])
		urlist = rlist.objects(id=request.user.id).first()

		itemlist = item.objects(id__in=urlist.rlist[skipnum:skipnum+15])
		orders = urlist.rlist[skipnum:skipnum+15]

		hasmore = True if len(orders) >= 15 else False
		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res = {}
		res['data'] = t.render(c)
		res['params'] = request.POST.copy()
		res['params']['start'] = repr(skipnum + len(itemlist))
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

	return render(request, 'rs_main.html', locals())

def lookclassify(request):
	col = 'lookclassify'
	param_c = request.GET.getlist('category[]',[])
	param_s = request.GET.getlist('source[]',[])
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {}
		res['params'] = request.POST.copy()
		skipnum = int(request.POST['start'])
		orderby = request.GET.get('orderby', 'time')
		if orderby == 'time':
			itemlist = item.objects( Q(source__in=param_s) | Q(category__in=param_c) )\
				.order_by("-pubdate").skip(skipnum).limit(15)
			hasmore = True if len(itemlist) >= 15 else False
			res['params']['start'] = repr(skipnum + len(itemlist))
		elif orderby == 'hot':
			itemlist = item.objects( Q(source__in=param_s) | Q(category__in=param_c) )\
				.order_by("-click_num").skip(skipnum).limit(15)
			hasmore = True if len(itemlist) >= 15 else False
			res['params']['start'] = repr(skipnum + len(itemlist))
		elif orderby == 'favo':
			itemlist = item.objects( Q(source__in=param_s) | Q(category__in=param_c) )\
				.order_by("-favo_num").skip(skipnum).limit(15)
			hasmore = True if len(itemlist) >= 15 else False
			res['params']['start'] = repr(skipnum + len(itemlist))
		else:
			itemlist = item.objects( (Q(source__in=param_s) | Q(category__in=param_c)) & \
				Q(pubdate__gte=now()-datetime.timedelta(days=10)) & \
				Q(rand__near=[random.random(), 0]) ).limit(15)
			hasmore = True if len(itemlist) >= 15 else False
			res['params']['start'] = 0

		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res['data'] = t.render(c)
		response.write( json.dumps(res, ensure_ascii=False) )
		return response
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
	response = HttpResponse()
	if request.method == 'POST':
		response['Content-Type'] = 'application/json'
		res = {}
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
		t = get_template('rs_category_source.html')
		c = Context(locals())
		res['data'] = t.render(c)
		response.write( json.dumps(res, ensure_ascii=False) )
	return response

def search(request):
	col = 'search'
	if request.method == 'POST':
		b = behavior(uid=request.user.id, action='search', \
			target=request.GET['wd'], timestamp=now())
		b.save()
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {}
		res['params'] = request.POST.copy()
		if 'searchid' not in request.POST:
			url = 'http://127.0.0.1:8899' + request.get_full_path()[3:]
			html = urllib2.urlopen(url).read()
			searchresponse = json.loads(html)
			if searchresponse['status'] == 'success':
				searchid = searchresponse['searchid']
				res['params']['searchid'] = searchid
				res['data'] = ''
			else :
				res['reason'] = searchresponse['reason']
				response.write( json.dumps(res, ensure_ascii=False) )
				return response
		else :
			searchid = request.POST['searchid']

		skipnum = int(request.POST['start'])
		slist = searchresult.objects(id=ObjectId(searchid)).first()
		itemlist = item.objects(id__in=slist.result[skipnum:skipnum+15])
		orders = slist.result[skipnum:skipnum+15]

		wd = request.GET['wd']
		hasmore = True if len(orders) >= 15 else False
		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res['data'] = t.render(c)
		res['params']['start'] = repr(skipnum + len(itemlist))
		response.write( json.dumps(res, ensure_ascii=False) )
		return response
	if 'wd' in request.GET:
		wd = request.GET['wd']
		return render(request, 'rs_main.html', locals())
	else :
		return HttpResponseRedirect('/rs/lookaround')

def updateSearchIndex(request):
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	url = 'http://127.0.0.1:8899/updateindex?pw=' + settings.params['search_password']
	try:
		res = urllib2.urlopen(url).read()		
	except :
		res = '{"reason":"SearchServer not available"}'
	response.write( res )	
	return response

def selffavorites(request):
	col = 'selffavorites'
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/account/login?redirecturl=/rs/selffavorites')
	if request.method == 'POST' and request.user.is_authenticated():
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		skipnum = int(request.POST['start'])
		if skipnum == 0:
			itemlist = item.objects(id__in=request.user.favorites[-15-skipnum:])
			orders = request.user.favorites[-15-skipnum:][::-1]
		else :
			itemlist = item.objects(id__in=request.user.favorites[-15-skipnum:-skipnum])
			orders = request.user.favorites[-15-skipnum:-skipnum][::-1]

		t = get_template('rs_itemlist.html')
		hasmore = True if len(itemlist) >= 15 else False
		c = Context(locals())
		res = {}
		res['data'] = t.render(c)
		res['params'] = request.POST.copy()
		res['params']['start'] = repr(skipnum + len(itemlist))
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

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
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	res = {}
	if request.method == 'POST':
		i = item.objects(id=request.POST['itemid']).first()
		b = behavior(uid=request.user.id,action='addtag',\
			target=request.POST['itemid'],timestamp=now())
		b.save()
		if request.POST['name'] not in i.tags:
			i.tags.append(request.POST['name'])
			i.save()
			tem = Template('''<a class="itemtag" target="_blank" 
				href="{% url 'lookclassified' %}?tag={{ t }}">#{{ t }}</span></a>''')
			res['data'] = tem.render( Context({'t': request.POST['name']}) )
	response.write( json.dumps(res, ensure_ascii=False) )
	return response

def getupre(request):
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	res = {}
	pre = upre.objects(id=request.user.id).first()
	if pre:
		if request.GET['target'] == 'source' and pre.source :
			res['data'] = map(lambda a:{'name':a[0],'count':a[1]}, \
				sorted(pre.source.iteritems(), key=lambda a:a[1], reverse=True))[:30]
		if request.GET['target'] == 'category' and pre.category :
			res['data'] = map(lambda a:{'name':a[0],'count':a[1]}, \
				sorted(pre.category.iteritems(), key=lambda a:a[1], reverse=True))[:30]
		if request.GET['target'] == 'wd' and pre.wd:
			res['data'] = map(lambda a:{'name':a[0],'count':a[1]}, \
				sorted(pre.wd.iteritems(), key=lambda a:a[1], reverse=True))[:100]
	response.write( json.dumps(res, ensure_ascii=False) )
	return response

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
