import urllib

from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from guardian.shortcuts import assign_perm, remove_perm

from po_translator.translation_management import data_processors

# to register data processors import them
from po_translator.translation_management.data_processors import (po, csv_file, xml_file)

from .models import (Language, Project, Set, SetMessage, SetList, ProjectLanguage)
from .utils import (get_message_list, import_po_file, save_same, site_admin,
                    save_same_target, save_new, show_prev, delete_last,
                    get_all_permissions, user_has_perm, get_sections_info)
from .forms import PoFileForm, MessageForm, ProjectForm, AddPermission
from .decorators import render_to_html, project_aware, render_to_json


@render_to_html('translation_management/project_list.html')
def home(request):
    request.session.modified = True
    return {}


def _set_var_to_path(request, name, value):
    if name in request.GET:
        return
    url = request.path
    request_key = {k: v for k, v in request.GET.iteritems()}
    request_key[name] = value
    url = "".join([url, '?', urllib.urlencode(
        {key: request_key[key].encode('utf8') for key in request_key})])
    return redirect(url)


@render_to_html('translation_management/project.html')
@project_aware
def project(request, project, lang_id=None):
    if request.method == 'POST':
        create_new_set(request, project)

    project_language = Language.objects.get(project=project)
    if not lang_id:
        return redirect('project', project_id=project.id, lang_id=project_language.id)

    current_proj = ProjectLanguage.objects.get(project=project, lang=Language.objects.get(id=lang_id))
    can_edit = site_admin(request.user) or request.user.has_perm('can_edit', current_proj)
    can_read = can_edit or request.user.has_perm('can_read', current_proj)
    if not can_read:
        django_messages.error(request, _("You haven't permission for this language in this project"))
        return redirect('home')
    
    for k, v in {'cur_section': '__none', 'translated': 'False'}.items():
        redirect_response = _set_var_to_path(request, k, v)
        if redirect_response:
            return redirect_response
    translated_filter = request.GET.get('translated', 'all')
    target_filters = {}
    stc_filters = {}
    section_filters = {}
    if 'cur_section' in request.GET:
        section_parts = ["%s." % request.GET.get('cur_section')] if request.GET.get('cur_section') else ['']
        if request.GET.get('cur_subsection'):
            section_parts.append("%s" % request.GET.get('cur_subsection'))
        stc_filters['msgid__startswith'] = "".join(section_parts)
        if request.GET['cur_section']:
            section_filters['msgid__startswith'] = section_parts[0]

    search_substring = ''
    if request.GET.get('substring'):
        search_substring = request.GET['substring']
        stc_filters[('msgid__icontains',
                     'msgstr__icontains')] = request.GET['substring']
        if stc_filters['msgid__startswith'] == '__none.':
            del stc_filters['msgid__startswith']

    if translated_filter in ('True', 'False'):
        target_filters['is_translated'] = translated_filter == 'True'
    messages = get_message_list(project.id,
                                lang_id,
                                target_filters=target_filters,
                                src_filters=stc_filters)
    sections, sub_sections = get_sections_info(project.id, lang_id, section_filters=section_filters)
    alter_languages = Language.objects.filter(projectlanguage__project_id=project).exclude(id=int(lang_id))
    context = {
        'translation': True,
        'message_list': messages,
        'sections': sections,
        'sub_sections': sub_sections,
        'search_substring': search_substring,
        'translated_filter': translated_filter,
        'cur_lang_name': Language.objects.get(id=lang_id).name,
        'cur_lang_id': int(lang_id),
        'source_lang': project_language.id,
        'source_lang_name': project_language.name,
        'form': MessageForm(),
        'alternative_languages_exists': alter_languages.exists(),
        'hide_subsection': not request.GET.get('cur_section'),
        'cur_section': request.GET.get('cur_section', None),
        'cur_subsection': request.GET.get('cur_subsection', None),
        'show_subsection': True and 'cur_subsection' in request.GET,
        'can_edit': can_edit
    }

    return context


@render_to_json
def update_msg(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid() and user_has_perm(request.user.pk, int(form.cleaned_data['id_of_message'])):
            new_msg = form.cleaned_data['msg_str']
            id_of_message = int(form.cleaned_data['id_of_message'])
            if request.POST['action'] == 'same':
                return save_same(id_of_message, new_msg)
            elif request.POST['action'] == 'new':
                return save_new(id_of_message, new_msg)
            elif request.POST['action'] == 'same_target':
                return save_same_target(id_of_message, new_msg, request.POST['is_translated'])
            elif request.POST['action'] == 'show_prev':
                return show_prev(id_of_message)
        return {'saved': False, 
                'message': "New meaning can't be empty",
                'prev_source': "You don't have permission",
                'prev_target': "You don't have permission"}
    return redirect('home')


def import_po_file_as_set(request, project, languages):
    errors = []
    if request.method == 'POST':
        form = PoFileForm(request.POST, request.FILES)
        form.fields['lang'].queryset = languages
        if form.is_valid():
            cur_lang = form.cleaned_data['lang']
            import_po_file(form.cleaned_data['pofile'], project.id, cur_lang.id)
            return redirect('project', project_id=project.id, lang_id=cur_lang.id)
        else:
            errors = form.errors.values()
    else:
        form = PoFileForm()
        form.fields['lang'].queryset = languages
    return {'form': form, 'errors': errors}


@render_to_html('translation_management/project.html')
@project_aware
def add_target_language(request, project):
    user = User.objects.get(id=request.user.pk)
    if not site_admin(user):
        django_messages.error(request, _("You can't add project language"))
        return redirect('home')

    if SetMessage.objects.filter(message_set__project_id=project).exists():
        languages = Language.objects.exclude(projectlanguage__project_id=project)
    else:
        proj_lang = project.lang.id
        languages = Language.objects.filter(id=proj_lang)

    context = import_po_file_as_set(request, project, languages)
    if not isinstance(context, dict):
        return context
    context.update({'show_import': True})
    return context


def create_new_set(request, project):
    user = User.objects.get(id=request.user.pk)
    if not site_admin(user):
        django_messages.error(request, _("You can't add project language"))
        return redirect('home')

    proj_lang = project.lang.id
    languages = Language.objects.filter(id=proj_lang)

    context = import_po_file_as_set(request, project, languages)
    if not isinstance(context, dict):
        django_messages.info(request, _("New set was created"))
        return context

    for i in context['errors']:
        for message in i:
            django_messages.warning(request, message)

    return context


@render_to_html('translation_management/project.html')
@project_aware
def export(request, project, language_id=None):
    if request.method == 'POST':
        language_id = int(request.POST['lang'])

    try:
        project_language = ProjectLanguage.objects.get(lang=language_id, project_id=project.id)

        dataset = get_message_list(project.id, language_id)
        for row in dataset:
            if not row['is_translated']:
                row['msg_target'] = row['msg_source']

        processor = data_processors.get_data_processor(project.project_type.name)
        export_response = processor.export_file(dataset, project_language.lang.code)

        return export_response
    except ProjectLanguage.DoesNotExist:
        errors = _('Set does not exist for this language')
        return {'errors': errors, 'show_export': True}


@render_to_html('translation_management/project.html')
@project_aware
def views_sets(request, project):
    user = User.objects.get(id=request.user.pk)
    can_delete = False
    if site_admin(user):
        can_delete = True
    if request.method == 'POST' and can_delete:
        delete_last(project.id)
        return redirect('views_sets', project_id=project.id)
    sets = []
    all_set = Set.objects.filter(project=project.id)
    for cur_set in all_set:
        sets.append({
            'message_set': cur_set.id,
            'name': cur_set.name,
            'created_at': cur_set.created_at,
            'len': SetList.objects.filter(message_set=cur_set.id).count()})
    return {'sets': sets, 'can_delete': can_delete, 'show_sets': True}


@render_to_html('translation_management/project.html')
@project_aware
def views_languages(request, project):
    sets = []
    all_lang = ProjectLanguage.objects.filter(project_id=project.id)
    for cur_set in all_lang:
        sets.append({'name': cur_set.lang.name, 'created_at': cur_set.created_at})
    return {'sets': sets, 'show_languages': True}


@render_to_html('translation_management/add_project.html')
def add_project(request):
    if not site_admin(request.user):
        django_messages.error(request, _("You can't add project language"))
        return redirect('home')
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            cur_lang = form.cleaned_data['lang']
            project = Project.objects.create(
                name=form.cleaned_data['name'],
                project_type=form.cleaned_data['project_type'],
                lang=cur_lang)
            if form.cleaned_data['pofile']:
                import_po_file(form.cleaned_data['pofile'], project.id, cur_lang.id)
            return redirect('cur_project', project_id=project.id)
    else:
        form = ProjectForm()
    return {'form': form}


def logout(request):
    auth.logout(request)
    return redirect('home')


@render_to_html('translation_management/project.html')
@project_aware
def views_permissions(request, project):
    user = User.objects.get(id=request.user.pk)
    can_add = False
    if site_admin(user):
        can_add = True
    if request.method == 'POST' and can_add:
        form = AddPermission(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user']
            lang_id = form.cleaned_data['lang']
            lang = Language.objects.get(id=lang_id)
            user = User.objects.get(id=user_id)
            project_language = ProjectLanguage.objects.get(project_id=project.id, lang=lang)
            project_source_language = Language.objects.get(project=project)
            project_source = ProjectLanguage.objects.get(project_id=project.id,
                                                         lang=project_source_language)
            if 'can_change' in request.POST['permission']:
                assign_perm('can_edit', user, project_language)
                assign_perm('can_read', user, project_language)
                assign_perm('can_read', user, project_source)
            elif 'can_read' in request.POST['permission']:
                assign_perm('can_read', user, project_language)
                remove_perm('can_edit', user, project_language)
                assign_perm('can_read', user, project_source)
            elif 'del_perm' in request.POST['permission']:
                remove_perm('can_edit', user, project_language)
                remove_perm('can_read', user, project_language)
    else:
        form = AddPermission()
    permissions = get_all_permissions(project.id)
    users = User.objects.all()
    return {
        'permissions': permissions,
        'show_permissions': True,
        'users': users,
        'can_add': can_add,
        'form': form
    }


@render_to_json
@project_aware
def get_subsection(request, project, lang_id):
    if 'cur_section' not in request.GET:
        url = request.path
        request_key = {k: v for k, v in request.GET}
        request_key['cur_section'] = ''
        url = "".join([url, '?', urllib.urlencode(request_key)])
        return redirect(url)

    project_language = Language.objects.get(project=project)
    lang_id = lang_id or project_language.id
    section_filters = {}
    sub_sections = []
    if 'cur_section' in request.GET:
        if request.GET.get('cur_section'):
            section = "%s." % request.GET.get('cur_section')
            section_filters['msgid__startswith'] = section

        _, sub_sections = get_sections_info(project.id, lang_id, section_filters=section_filters)
    return sub_sections
