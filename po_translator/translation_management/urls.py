from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('po_translator.translation_management.views',
    url(r'^$', 'home', name='home'),
    url(r'^project/(?P<project_id>\d+)/(?P<lang_id>\d+)/$', 'project', name='project'),
    url(r'^project/(?P<project_id>\d+)/(?P<lang_id>\d+)/get_subsection/$', 'get_subsection', name='get_subsection'),
    url(r'^cur_project/(?P<project_id>\d+)/$', 'project', name='cur_project'),
    url(r'^message/update/$', 'update_msg', name='update_msg'),
    url(r'^add_project/$', 'add_project', name='add_project'),
    url(r'^project/(?P<project_id>\d+)/create_language/$', 'add_target_language', name='add_target_language'),
    url(r'^project/(?P<project_id>\d+)/create_new_set/$', 'create_new_set', name='create_new_set'),
    url(r'^message/show_prev/$', 'show_prev', name='show_prev'),
    url(r'^project/(?P<project_id>\d+)/export/$', 'export', name='export'),
    url(r'^project/(?P<project_id>\d+)/export/(?P<language_id>\d+)/$', 'export', name='export_direct'),
    url(r'^project/(?P<project_id>\d+)/views/sets/$', 'views_sets', name='views_sets'),
    url(r'^project/(?P<project_id>\d+)/views/languages/$', 'views_languages', name='views_languages'),
    url(r'^project/(?P<project_id>\d+)/views/permissions/$', 'views_permissions', name='views_permissions'),
    url(r'^project/(?P<project_id>\d+)/views/sets/$', 'views_sets', name='views_sets'),
)
