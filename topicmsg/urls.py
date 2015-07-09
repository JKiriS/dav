from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'topicmsg.views.topiclist'),
    url(r'^topic', 'topicmsg.views.topicindex'),
    url(r'^msgdetail', 'topicmsg.views.getmsgdetail'),    
	url(r'^newtopicmodal$', 'topicmsg.views.newtopicmodal'),
	url(r'^createtopic$', 'topicmsg.views.createtopic'),
	url(r'^materiallist$', 'topicmsg.views.getmateriallist'),
    url(r'^addmaterial$', 'topicmsg.views.addmaterial'),
    url(r'^addmsg$', 'topicmsg.views.addmsg'),
    url(r'^getmsglist$', 'topicmsg.views.getmsglist'),
    # url(r'^lookaround', 'rs.views.lookaround', name='lookaround'),
)