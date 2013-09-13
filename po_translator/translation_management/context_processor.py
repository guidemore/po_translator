from models import (ProjectType, Language, PotrProject, PotrSet, PotrSetMessage,
                    PotrSetList, PotrImport, PotrImportMessage, PoFiles,
                    PotrProjectLanguage)


def common_data(request):
    projects = PotrProject.objects.all()

    if request.user.is_authenticated():
        user_name = '%s %s' % (request.user.first_name, request.user.last_name)
    else:
        user_name = False
    return {'projects': projects,
            'cur_proj_name': '',
            'languages': [],
            'user_name': user_name }
