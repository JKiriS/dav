from django.db import models
from mongoengine import *

# Create your models here.
class topic(Document):
	title = StringField()
	materials = ListField( ObjectIdField() )

	meta = {
		"db_alias": "default",
    }

class material(Document):
	title = StringField()
	url = URLField()
	content = StringField()
	version = FloatField()

	meta = {
		"db_alias": "default",
    }

class message(Document):
	user = DictField()
	topic = ObjectIdField()
	title = StringField()
	content = StringField()
	timestamp = DateTimeField()

	meta = {
		"db_alias": "default",
    }