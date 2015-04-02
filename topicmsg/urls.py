from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'topicmsg.views.index'),

    # url(r'^lookaround', 'rs.views.lookaround', name='lookaround'),
)