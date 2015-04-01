#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
import json
from django.http import HttpResponse, HttpResponseRedirect
from account.models import User, UserRegisterForm, UserLoginForm
from django.contrib import auth
from django.template import Template, Context
from django.views.decorators.csrf import csrf_protect
from dav.baseclasses import PostResponse

@csrf_protect
def register(request):
	if request.method == 'POST': 
		response = PostResponse()
		form = UserRegisterForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['uname']
			password = form.cleaned_data['pwd']
			email = form.cleaned_data['email']
			des = form.cleaned_data['des']
			if not User.objects.filter(email=email):
				user = User(username=username, email=email, des=des)
				user.set_password(password)  
				user.is_active = True  
				user.save()
			else :
				response.seterror([{'target':'email', 'reason':'该邮箱已被注册'},])
		else:
			errors = []
			for k in form.keys():
				errors.append({'target':k, 'reason':'输入无效'})
			response.seterror(errors)
		return response.get()
	return render(request, 'register.html')

@csrf_protect
def login(request):
	if request.method == 'POST':
		response = PostResponse()
		form = UserLoginForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			password = form.cleaned_data['pwd']
			user = User.objects(email=email).first()
			if user:
				username = user.username
				user = auth.authenticate(username=username, password=password)
				if user :
					if user.is_active:
						auth.login(request, user) 
						request.session.set_expiry(60 * 60 * 24 * 7)
						response.setparams('redirecturl', request.GET.get('redirecturl'))
					else :
						response.seterror([{'target':'email','reason':'该用户已被禁用，请联系管理员'},])
				else :
					response.seterror([{'target':'pwd','reason':'密码输入错误'},])
			else :
				response.seterror([{'target':'email','reason':'该邮箱尚未注册'},])
		else:
			errors = []
			for k in form.keys():
				errors.append({'target':k, 'reason':'输入无效'})
			response.seterror(errors)
		return response.get()
	return render(request, 'login.html')

def logout(request):
	auth.logout(request)
	return HttpResponseRedirect('/rs/')
