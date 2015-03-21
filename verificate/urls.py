from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'testsite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^getquestion$', 'verificate.views.getquestion'),
    url(r'^postselect$', 'verificate.views.collectselect'),
    url(r'^postmousetrail$', 'verificate.views.collectmousetrail'),
)