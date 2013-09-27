from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.utils.datastructures import SortedDict
from django.contrib.auth.models import User

from models import (Language, Project, Set, SetMessage,
                    SetList, Import, ImportMessage,
                    ProjectLanguage, ReadOnlyLastMessage)
from po_translator.translation_management import data_processors


def _update_message_query(initial_query, project_id, lang_id):
    project_language = Project.objects.get(id=project_id).lang.id
    cur_set = next(iter(Set.objects.filter(project_id=project_id).order_by('-id')), [])

    if not cur_set:
        return initial_query.empty()

    def db_field(model, field_name):
        table_name = model._meta.db_table
        return '.'.join([table_name, field_name])

    extra_where = ['%s=%s' % (db_field(ReadOnlyLastMessage, 'project_id'), project_id)]
    for f in ['message_set_id', 'msgid', 'lang_id']:
        extra_where.append('%s=%s' % (db_field(SetMessage, f), db_field(ReadOnlyLastMessage, f)))
    new_query = initial_query.extra(tables=[ReadOnlyLastMessage._meta.db_table], where=extra_where)
    new_query = new_query.extra(
        tables=[SetList._meta.db_table],
        where=['%s=%s' % (db_field(SetMessage, 'msgid'),
                          db_field(SetList, 'msgid')),
               '%s=%s' % (db_field(SetList, 'message_set_id'),
                          cur_set.id)])
    return new_query.filter(lang__in=[project_language, lang_id])


def get_sections_info(project_id, lang_id, section_filters={}):
    new_query = _update_message_query(SetMessage.objects.all(), project_id, lang_id)
    if not new_query.exists():
        return [], []

    all_section = {}
    for msgid in new_query.values('msgid'):
        all_section.setdefault(msgid['msgid'].split('.')[0], [])
        all_section[msgid['msgid'].split('.')[0]].append(msgid['msgid'].split('.')[1] if '.' in msgid['msgid'] else '')

    sections = all_section.keys()

    sub_sections = []
    if sections and section_filters and section_filters['msgid__startswith'] != '__none.':
        sub_sections = list(set(all_section[section_filters['msgid__startswith'][:-1]]))

    return sorted(sections), sorted(sub_sections)


def _spawn_query(key, value):
    if not isinstance(key, (list, tuple)):
        return Q(**{key: value})
    return reduce(lambda x, y: Q(**{y: value}) | x, key, Q())


def _normalize_filters(filters):
    return reduce(lambda x, y: _spawn_query(*y) & x, filters.items(), Q())


def get_message_list(project_id, lang_id, src_filters={}, target_filters={}):
    lang_id = int(lang_id)
    project_language = Project.objects.get(id=project_id).lang.id

    new_query = SetMessage.objects.all()

    if not new_query.exists():
        return []

    new_query = new_query.filter(_normalize_filters(src_filters))

    target_predicate = _normalize_filters(target_filters)
    if target_predicate:
        new_query = new_query.filter(Q(lang=project_language) | Q(target_predicate))

    res = SortedDict()

    new_query = _update_message_query(new_query, project_id, lang_id)

    for data in new_query.order_by('msgid'):
        msg_info = res.setdefault(data.msgid, {'msg_id': data.msgid})
        if data.lang_id == lang_id:
            msg_info.update(
                {
                    'msg_target': data.msgstr,
                    'target_id': data.id,
                    'is_translated': data.is_translated
                }
            )
        if data.lang_id == project_language:
            msg_info.update({'msg_source': data.msgstr, 'id': data.id})
    messages = [i for i in res.values() if 'msg_target' in i]
    return messages


def _create_new_set(project, lang_id, translations_data):
    potr_set = Set.objects.create(project=project, name='%s:%s' % (project.id, datetime.now()))

    potr_import = Import.objects.create(message_set=potr_set, lang_id=lang_id)
    for entry in translations_data:
        ImportMessage.objects.create(poimport=potr_import, msgid=entry["msgid"], msgstr=entry["msgstr"])
        find = SetList.objects.filter(message_set__project_id=project.id, msgid=entry["msgid"]).exists()
        SetList.objects.create(message_set=potr_set, msgid=entry["msgid"], msgstr=entry["msgstr"])
        if not find:
            SetMessage.objects.create(message_set=potr_set,
                                      lang_id=lang_id,
                                      msgid=entry["msgid"],
                                      msgstr=entry["msgstr"],
                                      is_translated=True)


def _import_new_lang(project, lang_id, translations_data):
    potr_set = Set.objects.filter(project=project).order_by('-id')[0]

    potr_import = Import.objects.create(message_set=potr_set, lang_id=lang_id)
    for entry in translations_data:
        ImportMessage.objects.create(poimport=potr_import,
                                     msgid=entry["msgid"],
                                     msgstr=entry["msgstr"])
        if not SetList.objects.filter(message_set__project_id=project.id,
                                      message_set=potr_set.id,
                                      msgid=entry["msgid"]).exists():
            continue
        SetMessage.objects.create(message_set=potr_set,
                                  lang_id=lang_id,
                                  msgid=entry["msgid"],
                                  msgstr=entry["msgstr"],
                                  is_translated=False)
    for msg in SetList.objects.filter(message_set__project_id=project.id, message_set=potr_set.id):
        if SetMessage.objects.filter(message_set=potr_set.id, lang_id=lang_id, msgid=msg.msgid).exists():
            continue
        SetMessage.objects.create(message_set=potr_set,
                                  lang_id=lang_id,
                                  msgid=msg.msgid,
                                  msgstr=msg.msgstr,
                                  is_translated=False)


@transaction.commit_on_success
def import_po_file(message_file, project_id, lang_id):
    ProjectLanguage.objects.get_or_create(
        lang=Language.objects.get(id=lang_id),
        project=Project.objects.get(id=project_id))
    project = Project.objects.filter(id=project_id)[0]

    data_processor = data_processors.get_data_processor(project.project_type.name)
    translations_data = data_processor.parse_file(message_file)

    if int(lang_id) == int(project.lang_id):
        _create_new_set(project, lang_id, translations_data)
    else:
        _import_new_lang(project, lang_id, translations_data)


@transaction.commit_on_success
def save_same(msg_id, new_msg):
    SetMessage.objects.filter(id=msg_id).update(msgstr=new_msg)
    for item in SetMessage.objects.filter(id=msg_id):
        item.save()
    return {'saved': True}


@transaction.commit_on_success
def save_same_target(msg_id, new_msg, is_translated):
    if is_translated == "True":
        is_translated = True
    else:
        is_translated = False

    new_item = SetMessage.objects.filter(id=msg_id)[0]
    project_id = new_item.message_set.project
    last_set = Set.objects.filter(project=project_id).order_by('-id')[0]
    if SetMessage.objects.filter(id=msg_id)[0].message_set == last_set:
        (SetMessage.objects.filter(id=msg_id).update(msgstr=new_msg, is_translated=is_translated))
        for item in SetMessage.objects.filter(id=msg_id):
            item.save()
    else:
        SetMessage.objects.create(message_set=last_set,
                                  lang=new_item.lang,
                                  msgid=new_item.msgid,
                                  msgstr=new_msg,
                                  is_translated=is_translated)
    return {'saved': True}


@transaction.commit_on_success
def save_new(msg_id, new_msg):
    new_item = SetMessage.objects.filter(id=msg_id)[0]
    msgid = new_item.msgid
    project_id = new_item.message_set.project.id
    last_set = Set.objects.filter(project=project_id).order_by('-id')[0]
    obj, created = SetMessage.objects.get_or_create(message_set=last_set, lang=new_item.lang, msgid=msgid)
    obj.msgstr = new_msg
    obj.is_translated = True
    obj.save()
    (SetMessage.objects.filter(message_set=last_set.id, msgid=msgid)
     .exclude(id=msg_id)
     .update(is_translated=False))
    for lang in ProjectLanguage.objects.filter(project_id=project_id).exclude(lang=new_item.lang):
        target_msg_kwargs = dict(msgid=msgid, lang=lang.lang)
        new_target, _ = SetMessage.objects.get_or_create(
            message_set=last_set,
            defaults={'msgstr': new_msg, 'is_translated': False},
            **target_msg_kwargs)
        previous_msgs = (SetMessage.objects
                         .filter(**target_msg_kwargs)
                         .exclude(id=msg_id)
                         .order_by('-id'))
        if previous_msgs.count() > 1:
            new_target.msgstr = previous_msgs[1].msgstr
            new_target.save()
    return {'saved': True}


def show_prev(msg_id):
    message = SetMessage.objects.get(id=msg_id)
    project = message.message_set.project
    last_set = message.message_set
    lang = message.lang
    project_language = message.message_set.project.lang
    resp = {}

    for language, resp_field in [(project_language, 'prev_source'), (lang, 'prev_target')]:
        prev_value = (SetMessage.objects
                      .filter(msgid=message.msgid, message_set__project=project, lang=language)
                      .exclude(message_set=last_set)
                      .order_by('-id'))
        prev_value = next(iter(prev_value), None)
        resp[resp_field] = (prev_value.msgstr if prev_value else 'no information')
    return resp


def delete_last(project_id):
    if not Set.objects.filter(project=project_id).count():
        return

    last_set = Set.objects.filter(project=project_id).order_by('-id')[0]
    SetMessage.objects.filter(message_set=last_set.id).delete()
    SetList.objects.filter(message_set=last_set.id).delete()
    ImportMessage.objects.filter(poimport__message_set=last_set.id).delete()
    Import.objects.filter(message_set=last_set.id).delete()
    Set.objects.filter(id=last_set.id).delete()


def get_all_permissions(project_id):
    project_languages = ProjectLanguage.objects.filter(project__id=project_id)
    result = []
    for lang in project_languages:
        project = ProjectLanguage.objects.get(project__id=project_id, lang=lang.lang.id)
        for user in User.objects.all():
            result.append(
                {
                    'lang': lang.lang.name,
                    'user': user.username,
                    'can_change': user.has_perm('can_edit', project),
                    'can_read': user.has_perm('can_read', project),
                    'site_admin': site_admin(user)
                }
            )
    return result

def site_admin(user):
    if user.groups.filter(name='admin').exists() or user.is_superuser:
        return True
    return False

def user_has_perm(user_id, id_of_message):
    mes = SetMessage.objects.get(id=id_of_message)
    project = ProjectLanguage.objects.get(project__id=mes.message_set.project.id, lang=mes.lang.id)
    user = User.objects.get(id=user_id)
    if user.has_perm('can_edit', project) or site_admin(user):
        return True
    else:
        return False