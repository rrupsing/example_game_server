from django.conf.urls import patterns, include, url
from django_server.rooms import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^join_room', views.join_room),
)