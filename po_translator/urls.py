from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import po_translator.translation_management

admin.autodiscover()


urlpatterns = patterns('',
    # existing patterns here...
    (r'^login/$',  login, {'template_name': 'login.html'}),
    url(r'^login/external/', include('social_auth.urls', app_name='social_auth')),
    url(r'^logout/$', logout, name='logout'),
    )

urlpatterns += patterns('',
    # Examples:
    # url(r'^po_translator/', include('po_translator.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('po_translator.translation_management.urls')),
)
