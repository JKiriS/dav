from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'testsite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^register', 'account.views.register', name='register'),
    url(r'^login', 'account.views.login', name='login'),
    url(r'^logout', 'account.views.logout', name='logout'),
)