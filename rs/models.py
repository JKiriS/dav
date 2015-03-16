from django.db import models
from mongoengine import *

# Create your models here.

class source(Document):
	name = StringField()

class tag(Document):
	name = StringField()

class item(Document):
	title = StringField()
	link = URLField()
	pubdate = DateTimeField()
	source = StringField()
	category = StringField()
	tags = ListField( StringField() )
	des = StringField()
	imgurl = URLField()
	rand = PointField()
	click_num = IntField(default=0)
	favo_num = IntField(default=0)

	meta = {
		"db_alias": "default",
    }

class site(Document):
	url = URLField()
	handler = StringField()
	source = StringField()
	tags = ListField( StringField() )
	latest = DateTimeField()

	meta = {'db_alias':'default'}

class behavior(Document):
	uid = ObjectIdField()
	action = StringField()
	target = StringField()
	timestamp = DateTimeField()
	fromurl = StringField()

	meta = {"db_alias": "default"}

class rlist(Document):
	rlist = ListField( ObjectIdField() )

	meta = {"db_alias": "default"}

class upre(Document):
	source = DictField()
	category = DictField()
	wd = DictField()

	meta = {"db_alias": "default"}

class searchresult(Document):
	wd = StringField()
	result = ListField( ObjectIdField() )
	click = ListField( ObjectIdField() )
	timestamp = DateTimeField()

	meta = {'db_alias':'default'}