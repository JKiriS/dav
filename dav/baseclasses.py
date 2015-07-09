from django.shortcuts import render
import json
from django.http import HttpResponse
from django.template import Context


class PostResponse:
	def __init__(self, POST=None):
		self.response = HttpResponse()
		self.response['Content-Type'] = 'application/json'
		self.result = {'data':None,'errors':None}
		if POST:
			self.result['params'] = POST.copy()
	def render(self, t, c):
		self.result['data'] = t.render(Context(c))
	def setparams(self, pn, value):
		if not self.result.get('params'):
			self.result['params'] = {}
		self.result['params'][pn] = value
	def get(self):
		self.response.write( json.dumps(self.result, ensure_ascii=False) )
		return self.response
	def seterror(self, e):
		self.result['error'] = e
	def setdata(self, d):
		self.result['data'] = d