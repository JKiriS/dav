#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
import json
from django.http import HttpResponse, HttpResponseRedirect
from account.models import User, UserRegisterForm, UserLoginForm
from django.contrib import auth
from django.template import Template, Context
from django.views.decorators.csrf import csrf_protect
#from mongoengine.django.auth import User

# Create your views here.

@csrf_protect
def register(request):
	if request.method == 'POST': 
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {'status':'failed'}
		form = UserRegisterForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['uname']
			password = form.cleaned_data['pwd']
			email = form.cleaned_data['email']
			des = form.cleaned_data['des']
			if not User.objects.filter(email=email):
				user = User(username=username, email=email, des=des)
				user.set_password(password)  
				user.is_active=True  
				user.save()
				res['status'] = 'success'
		response.write( json.dumps(res, ensure_ascii=False) )
		return response
	return render(request, 'register.html')

@csrf_protect
def login(request):
	if request.method == 'POST':
		response = HttpResponse()
		response['Content-Type'] = 'application/json'
		res = {'status':'failed'}
		form = UserLoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['uname']
			password = form.cleaned_data['pwd']
			user = auth.authenticate(username=username, password=password)
			if user and user.is_active:
				auth.login(request, user) 
				request.session.set_expiry(60 * 60 * 24 * 7)
				res['status'] = 'success'
				res['redirecturl'] = request.GET.get('redirecturl')
		response.write( json.dumps(res, ensure_ascii=False) )
		return response
	return render(request, 'login.html')

def logout(request):
	auth.logout(request)
	return HttpResponseRedirect('/rs/')
