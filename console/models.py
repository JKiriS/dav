from django.db import models
from mongoengine import *

# Create your models here.

class site(Document):
	url = URLField()
	parser = StringField()
	source = StringField()
	category = StringField()
	tags = ListField( StringField() )
	latest = DateTimeField()
	status = StringField(default='enabled')

	meta = {'db_alias':'default'}

class job(Document):
	function = StringField()
	starttime = DateTimeField()
	status = StringField(default='waiting')

	meta = {'db_alias':'default'}