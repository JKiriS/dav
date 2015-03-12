#from django.db import models

from mongoengine import *
from django import forms

# Create your models here.
from mongoengine.django.auth import User

class User(User):
	des = StringField()
	favorites = ListField( ObjectIdField() )

	meta = {"db_alias": "default"}

class UserRegisterForm(forms.Form):
	uname = forms.CharField(label=(u'uname'),max_length=30,widget=forms.TextInput(attrs={'size': 20,}))      
 	pwd = forms.CharField(label=(u'pwd'),max_length=30,widget=forms.PasswordInput(attrs={'size': 20,}))  
	email = forms.EmailField(label=(u'email'),max_length=30,widget=forms.TextInput(attrs={'size': 30,}))
	des = forms.CharField(label=(u'des'),max_length=30,widget=forms.TextInput(attrs={'size': 20,}),required=False)

class UserLoginForm(forms.Form):
	email = forms.EmailField(label=(u'email'),max_length=30,widget=forms.TextInput(attrs={'size': 30,}))
 	pwd = forms.CharField(label=(u'pwd'),max_length=30,widget=forms.PasswordInput(attrs={'size': 20,}))  

