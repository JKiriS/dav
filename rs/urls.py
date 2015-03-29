from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'rs.views.index'),

    url(r'^lookaround', 'rs.views.lookaround', name='lookaround'),
    url(r'^recommend', 'rs.views.recommend', name='recommend'),
    url(r'^lookclassify', 'rs.views.lookclassify', name='lookclassify'),
    url(r'^search', 'rs.views.search', name='search'),
    url(r'^selffavorites', 'rs.views.selffavorites', name='selffavorites'),
    url(r'^selfpre', 'rs.views.selfpre', name='selfpre'),

    url(r'^behaviorrecorder$', 'rs.views.behaviorrecorder'),
    url(r'^additemtag', 'rs.views.additemtag'),
    url(r'^getupre', 'rs.views.getupre'),
    url(r'^getcs', 'rs.views.getcs'),
    url(r'^addfavorite', 'rs.views.addfavorite'),
    url(r'^removefavorite', 'rs.views.removefavorite'),
)