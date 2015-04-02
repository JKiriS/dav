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
 

# Create your views here.
now = lambda : datetime.datetime.utcnow()

def index(request):
	return render(request, 'topicmsg_main.html', locals())

def getmateriallist(request):
	if request.method == 'POST':
		response = PostResponse()
		target = request.GET['topic']
		t = topic.objects(id=ObjectId(target)).first()
		if not t:
			pass
		orders = t.materials[::-1]
		materiallist = material.objects(id__in=orders)
		tem =  Template('''
			{% for m in materiallist%}
				<a href="{{ m.url }}" class="material">{{ m.title }}</a>
			{% endfor %}
			''')
		response.render(tem, locals())
		return response.render(tem, locals())

def addmaterial(request):
	if request.method == 'POST':
		response = PostResponse()
		target = request.GET['topic']
		url = request.POST['url']
		title = request.POST['title']
		mat = material(url=url, title=title)
		t = topic.objects(id=ObjectId(target)).first()
		if not t:
			pass
		msg = message(topic=t.id,title=u"添加了新资料",timestamp=now(),
			content='<a href="{}">{}</a>'.format(mat.url,mat.title),
			user={'uid':request.user.id,'name':request.user.uername})
		msg.append()
		t.materials.append(m.id)
		t.save()
		mat.save()
		tem =  Template('''
			<a href="{{ mat.url }}" class="material">{{ mat.title }}</a>
			''')
		response.render(tem, locals())
		return response.get()