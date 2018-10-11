from django.conf.urls import url

from . import views

app_name = 'blog'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^post/(?P<pk>[0-9]+)/$', views.PostDetailView.as_view(), name='detail'),
    url(r'^archives/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/$', views.ArchivesView.as_view(), name='archives'),
    url(r'^category/(?P<pk>[0-9]+)/$', views.CategoryView.as_view(), name='category'),
    url(r'^tag/(?P<pk>[0-9]+)/$', views.TagView.as_view(), name='tag'),
    # url(r'^search/$', views.search, name='search'),
    url(r'^qk/$', views.qk),
    url(r'^wxpost/(?P<pk>[0-9]+)/$',views.getDetail),
    url(r'^wxlist/$',views.getList),
    url(r'^getimgs/$', views.getimgs),
    url(r'^getavatar/$', views.getavatar),
    url(r'^getwallpaper/$', views.getwallpaper),
]
