from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'dav.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^map/', include('mapv.urls')),
    url(r'^history/', include('historyv.urls')),
    url(r'^rs/', include('rs.urls')),
    url(r'.*/(?P<fname>.*)\.json$', 'dav.views.sendjson'),
    url(r'^account/', include('account.urls')),
)
