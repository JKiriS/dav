#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from rs.models import item, behavior, tag, rlist, upre, source, searchresult
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

# load and handle categories
def csload():
	csfile =  file(os.path.join(settings.BASE_DIR, "rsbackend/categories.json"))
	return json.load(csfile)
def cssearch(target=u'综合', tree=csload()):
	if tree['name'] == target:
		return csgather(tree, [])
	else :
		if 'children' in tree:
			for i in tree['children']:
				res = cssearch(target, i)
				if len(res) > 0:
					return res
	return []
def csgather(tree=csload(), res=[]):
	res.append(tree['name'])
	if 'children' in tree:
		for i in tree['children']:
			csgather(i, res)
	return res

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
		skipnum = int(request.POST['start'])
		# itemlist = item.objects().order_by("-pubdate").skip(skipnum).limit(15).clone()
		itemlist = item.objects(pubdate__gte=now()-datetime.timedelta(days=5),rand__near=[random.random(), 0]).limit(15)
		hasmore = True if len(itemlist) >= 15 else False
		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res = {}
		res['data'] = t.render(c)
		res['params'] = request.POST.copy()
		res['params']['start'] = repr(skipnum + len(itemlist))
		res['status'] = 'success'
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

		hasmore = True if len(itemlist) >= 15 else False
		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res = {}
		res['data'] = t.render(c)
		res['params'] = request.POST.copy()
		res['params']['start'] = repr(skipnum + len(itemlist))
		res['status'] = 'success'
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

	return render(request, 'rs_main.html', locals())

def lookclassifiedRecorder(request):
	if request.user.is_authenticated():
		b = behavior(uid=request.user.id, action='search', timestamp=now())
		if 'source' in request.GET:
			b.ttype = 'source'
			b.target = request.GET['source']
		elif 'category' in request.GET:
			b.ttype = 'category'
			b.target = request.GET['category']
		elif 'wd' in request.GET:
			b.ttype = 'wd'
			b.target = request.GET['wd']
		else :
			return
		b.save()
def classifiedHandler(request, skipnum):
	if 'source' in request.GET:
		itemlist = item.objects(source=request.GET['source'])\
			.order_by("-pubdate").skip(skipnum).limit(15)
	elif 'category' in request.GET:
		itemlist = item.objects(category__in=cssearch(request.GET['category']))\
			.order_by("-pubdate").skip(skipnum).limit(15)
	else :
		itemlist = item.objects().limit(0)
	return itemlist
def lookclassified(request):
	col = 'lookclassified'
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		lookclassifiedRecorder(request)
		skipnum = int(request.POST['start'])
		itemlist = classifiedHandler(request, skipnum)
		hasmore = True if len(itemlist) >= 15 else False
		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res = {}
		res['data'] = t.render(c)
		res['params'] = request.POST.copy()
		res['params']['start'] = repr(skipnum + len(itemlist))
		res['status'] = 'success'
		response.write( json.dumps(res, ensure_ascii=False) )
		return response
	if 'source' in request.GET:
		classname = request.GET['source']
		return render(request, 'rs_main.html', locals())
	elif 'category' in request.GET:
		classname = request.GET['category']
		return render(request, 'rs_main.html', locals())
	else:
		return HttpResponseRedirect('/rs/lookaround')

def search(request):
	col = 'search'
	if request.method == 'POST':
		lookclassifiedRecorder(request)
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {'status':'failed'}
		res['params'] = request.POST.copy()
		if 'searchid' not in request.POST:
			url = 'http://127.0.0.1:8899' + request.get_full_path()[3:]
			html = urllib2.urlopen(url).read()
			searchresponse = json.loads(html)
			if searchresponse['status'] == 'success':
				searchid = searchresponse['searchid']
				res['params']['searchid'] = searchid
			else :
				res['reason'] = searchresponse['reason']
				res['data'] = ''
				response.write( json.dumps(res, ensure_ascii=False) )
				return response
		else :
			searchid = request.POST['searchid']

		skipnum = int(request.POST['start'])
		slist = searchresult.objects(id=ObjectId(searchid)).first()
		itemlist = item.objects(id__in=slist.result[skipnum:skipnum+15])
		orders = slist.result[skipnum:skipnum+15]

		wd = request.GET['wd']
		hasmore = True if len(itemlist) >= 15 else False
		t = get_template('rs_itemlist.html')
		c = Context(locals())
		res['data'] = t.render(c)
		res['params']['start'] = repr(skipnum + len(itemlist))
		res['status'] = 'success'

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
		res = '{"status":"failed", "reason":"SearchServer not available"}'
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
		itemlist = item.objects(id__in=request.user.favorites[skipnum:skipnum+15])
		orders = request.user.favorites[skipnum:skipnum+15][::-1]

		t = get_template('rs_itemlist.html')
		hasmore = True if len(itemlist) >= 15 else False
		c = Context(locals())
		res = {}
		res['data'] = t.render(c)
		res['params'] = request.POST.copy()
		res['params']['start'] = repr(skipnum + len(itemlist))
		res['status'] = 'success'
		response.write( json.dumps(res, ensure_ascii=False) )
		return response

	return render(request, 'rs_main.html', locals())

def selfpre(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/account/login?redirecturl=/rs/selfpre')
	return render(request, 'rs_selfpre.html', locals())

def behaviorrecorder(request):
	if request.method == 'POST': 
		if 	request.user.is_authenticated():
			b = behavior(uid=request.user.id, action='click', ttype='item',\
				target=request.POST['target'], timestamp=now(), 
				fromurl = request.POST['fromurl'])
			b.save()
		if 'searchid' in request.POST:
			sr = searchresult.objects(id=request.POST['searchid']).first()
			sr.click.append( ObjectId(request.POST['target']) )
			sr.save()
	return HttpResponse()

def additemtag(request):
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	res = {'status':'failed'}
	if request.method == 'POST':
		i = item.objects(id=request.POST['itemid']).first()
		if request.user.is_authenticated():
			b = behavior(uid=request.user.id,action='add',ttype='tag',\
				target=request.POST['name'],timestamp=now())
			b.save()
			b = behavior(uid=request.user.id,action='addtag',ttype='item',\
				target=request.POST['itemid'],timestamp=now())
			b.save()
		if request.POST['name'] not in i.tags:
			i.tags.append(request.POST['name'])
			i.save()
			tem = Template('''<a class="itemtag" target="_blank" 
				href="{% url 'lookclassified' %}?tag={{ t }}">#{{ t }}</span></a>''')
			res['data'] = tem.render( Context({'t': request.POST['name']}) )
			res['status'] = 'success'
	response.write( json.dumps(res, ensure_ascii=False) )
	return response

def getupre(request):
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	res = {'status':'failed'}
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
		res['status'] = 'success'
	response.write( json.dumps(res, ensure_ascii=False) )
	return response

def getsource(request):
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	res = {'status':'success'}
	res['data'] = []
	for i in source.objects():
		res['data'].append(i.name)
	response.write( json.dumps(res, ensure_ascii=False) )
	return response

def getcategory(request):
	response = HttpResponse()
	response['Content-Type'] = 'application/json'
	res = {'status':'success'}
	res['data'] = csgather(csload(), [])
	response.write( json.dumps(res, ensure_ascii=False) )
	return response

def addfavorite(request):
	if request.user.is_authenticated():
		target = request.POST.get('target')
		request.user.favorites.append( ObjectId(target) )
		request.user.save()
		b = behavior(uid=request.user.id, action='addfavorite', ttype='item',\
			target=request.POST['target'], timestamp=now())
		b.save()
	return HttpResponse()

def removefavorite(request):
	if request.user.is_authenticated():
		target = request.POST.get('target')
		request.user.favorites.remove( ObjectId(target) )
		request.user.save()
		b = behavior(uid=request.user.id, action='removefavorite', ttype='item',\
			target=request.POST['target'], timestamp=now())
		b.save()
	return HttpResponse()
