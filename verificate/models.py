from django.db import models
from mongoengine import *
import datetime

# Create your models here.

class verification(Document):
	question = StringField()
	option = ListField( StringField() )
	selection = ListField( IntField(), default=[] )
	rand = PointField()

	meta = {
		"db_alias": "default",
    }

class mousetrail(Document):
	uid = ObjectIdField()
	timestamp = DateTimeField(default=datetime.datetime.now())
	traildata = ListField( StringField() )
	useragent = StringField()
	
	meta = {
		"db_alias": "default",
    }

