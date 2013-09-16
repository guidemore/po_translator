from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login/$',  login, {'template_name': 'po_translator/login.html'}, name='login'),
    url(r'^login/external/', include('social_auth.urls', app_name='social_auth')),
    url(r'^logout/$', logout, name='logout'),
)

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('po_translator.translation_management.urls')),
)
