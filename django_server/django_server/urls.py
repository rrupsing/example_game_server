from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_server.views.home', name='home'),
    # url(r'^django_server/', include('django_server.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^get_or_create_user', 'django_server.views.create_user', name = 'create_user'),
	url(r'^get_friends', 'django_server.views.get_friends', name = 'get_friends'),
    url(r'^room/?', include('django_server.room.urls')),

)
