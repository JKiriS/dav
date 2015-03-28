from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'testsite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^rs$', 'console.views.rsconsole', name='rsconsole'),
    url(r'^getservices', 'console.views.getservices'),
    url(r'^setservices', 'console.views.setservices'),
    url(r'^getsites', 'console.views.getsites'),
    url(r'^setsites', 'console.views.setsites'),
    url(r'^getjobs', 'console.views.getjobs'),
    url(r'^setjobs', 'console.views.setjobs'),
    
)