from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import json
from django.utils import simplejson
import settings
import os.path
# Create your views here.


def sendjson(request, fname):
	fpath = os.path.join(settings.BASE_DIR, "static/json/", fname+'.json')
	try:
		f = file(fpath)
		s = json.load(f)
		f.close()
	except Exception, e:
		s = {'error':'file '+fpath+'.json not found'}
	return HttpResponse(simplejson.dumps(s, ensure_ascii=False))