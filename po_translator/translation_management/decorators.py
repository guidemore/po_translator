import functools
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from .models import Project, ProjectLanguage
import json
from django.http import HttpResponse

def render_to_html(template_name):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(request, *atgs, **kwargs):
            result = func(request, *atgs, **kwargs)
            if isinstance(result, dict):
                return render_to_response(template_name, result,
                                          RequestContext(request))
            return result
        return wrapped
    return wrapper

def project_aware(func):
    @functools.wraps(func)
    def wrapped(request, project_id, *atgs, **kwargs):
        project = Project.objects.get(id=project_id)
        result = func(request, project, *atgs, **kwargs)
        if isinstance(result, dict):
            languages = ProjectLanguage.objects.filter(project=project)
            result.update({'project_id': project_id,
                           'cur_proj_name': project.name,
                           'languages': languages})
        return result
    return wrapped

def render_to_json(func):
    @functools.wraps(func)
    def wrapped(request, *atgs, **kwargs):
        result = func(request, *atgs, **kwargs)
        if isinstance(result, (dict,list)):
            return HttpResponse(json.dumps(result))
        return result
    return wrapped