from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.utils.datastructures import SortedDict
from models import (Language, PotrProject, PotrSet, PotrSetMessage,
                    PotrSetList, PotrImport, PotrImportMessage,
                    PotrProjectLanguage, ReadOnlyLastMessage)
from django.contrib.auth.models import User

from po_translator.translation_management import data_processors


def _update_message_query(initial_query, project_id, lang_id):
    proj_lang = PotrProject.objects.get(id=project_id).lang.id
    cur_set = next(iter(PotrSet.objects.filter(project_id=project_id)
                                       .order_by('-id')), [])

    if not cur_set:
        return initial_query.filter(id=-1) #  return empty set

    def db_field(model, field_name):
        table_name = model._meta.db_table
        return '.'.join([table_name, field_name])

    extra_where = ['%s=%s' % (db_field(ReadOnlyLastMessage, 'project_id'),
                              project_id)]
    for f in ['message_set_id', 'msgid', 'lang_id']:
        extra_where.append('%s=%s' % (db_field(PotrSetMessage, f),
                                      db_field(ReadOnlyLastMessage, f)))
    new_query = initial_query.extra(
                  tables=[ReadOnlyLastMessage._meta.db_table],
                  where=extra_where)
    new_query = new_query.extra(
                  tables=[PotrSetList._meta.db_table],
                  where=['%s=%s' % (db_field(PotrSetMessage, 'msgid'),
                                    db_field(PotrSetList, 'msgid')),
                         '%s=%s' % (db_field(PotrSetList, 'message_set_id'),
                                    cur_set.id)])
    return new_query.filter(lang__in=[proj_lang, lang_id])


def get_sections_info(project_id, lang_id, section_filters={}):
    new_query = _update_message_query(PotrSetMessage.objects.all(),
                                      project_id, lang_id)
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

def get_message_list(project_id, lang_id,
                     src_filters={}, target_filters={}):
    lang_id = int(lang_id)
    proj_lang = PotrProject.objects.get(id=project_id).lang.id

    new_query = PotrSetMessage.objects.all()

    if not new_query.exists():
        return []

    new_query = new_query.filter(_normalize_filters(src_filters))

    target_predicate = _normalize_filters(target_filters)
    if target_predicate:
        new_query = new_query.filter(Q(lang=proj_lang) | Q(target_predicate))

    res = SortedDict()

    new_query = _update_message_query(new_query, project_id, lang_id)

    for data in new_query.order_by('msgid'):
        msg_info = res.setdefault(data.msgid, {'msg_id': data.msgid})
        if data.lang_id == lang_id:
            msg_info.update({'msg_target': data.msgstr,
                             'target_id': data.id,
                             'is_translated': data.is_translated})
        if data.lang_id == proj_lang:
            msg_info.update({'msg_source': data.msgstr, 'id': data.id})
    messages = [i for i in res.values() if 'msg_target' in i]
    return messages


def _create_new_set(proj, lang_id, translations_data):
    potr_set = PotrSet.objects.create(project_id=proj,
                                      name='%s:%s' % (proj.id, datetime.now()))

    potr_import = PotrImport.objects.create(message_set=potr_set,
                                            lang_id=lang_id)
    for entry in translations_data:
        PotrImportMessage.objects.create(import_id=potr_import,
                                         msgid=entry["msgid"],
                                         msgstr=entry["msgstr"])
        find = PotrSetList.objects.filter(message_set__project_id=proj.id,
                                          msgid=entry["msgid"]).exists()
        PotrSetList.objects.create(message_set=potr_set,
                                   msgid=entry["msgid"],
                                   msgstr=entry["msgstr"])
        if not find:
            PotrSetMessage.objects.create(message_set=potr_set,
                                          lang_id=lang_id,
                                          msgid=entry["msgid"],
                                          msgstr=entry["msgstr"],
                                          is_translated=True)

def _import_new_lang(proj, lang_id, translations_data):
    potr_set = PotrSet.objects.filter(project_id=proj).order_by('-id')[0]

    potr_import = PotrImport.objects.create(message_set=potr_set,
                                            lang_id=lang_id)
    for entry in translations_data:
        PotrImportMessage.objects.create(import_id=potr_import,
                                         msgid=entry["msgid"],
                                         msgstr=entry["msgstr"])
        if not PotrSetList.objects.filter(message_set__project_id=proj.id,
                                          message_set=potr_set.id,
                                          msgid=entry["msgid"]).exists():
            continue
        PotrSetMessage.objects.create(message_set=potr_set,
                                      lang_id=lang_id,
                                      msgid=entry["msgid"],
                                      msgstr=entry["msgstr"],
                                      is_translated=False)
    for msg in PotrSetList.objects.filter(message_set__project_id=proj.id,
                                          message_set=potr_set.id):
        if PotrSetMessage.objects.filter(message_set=potr_set.id,
                                         lang_id=lang_id,
                                         msgid=msg.msgid).exists():
            continue
        PotrSetMessage.objects.create(message_set=potr_set,
                                      lang_id=lang_id,
                                      msgid=msg.msgid,
                                      msgstr=msg.msgstr,
                                      is_translated=False)


@transaction.commit_on_success
def import_po_file(message_file, project_id, lang_id):
    PotrProjectLanguage.objects.get_or_create(
                            lang=Language.objects.get(id=lang_id),
                            project_id=PotrProject.objects.get(id=project_id))
    proj = PotrProject.objects.filter(id=project_id)[0]

    data_processor = data_processors.get_data_processor(proj.project_type.name)
    translations_data = data_processor.parse_file(message_file)

    if int(lang_id) == int(proj.lang_id):
        _create_new_set(proj, lang_id, translations_data)
    else:
        _import_new_lang(proj, lang_id, translations_data)


@transaction.commit_on_success
def save_same(msg_id, new_msg):
    PotrSetMessage.objects.filter(id=msg_id).update(msgstr=new_msg)
    for item in PotrSetMessage.objects.filter(id=msg_id):
        item.save()
    return {'saved': True}


@transaction.commit_on_success
def save_same_target(msg_id, new_msg, is_translated):
    if is_translated == "True":
        is_translated = True
    else:
        is_translated = False

    new_item = PotrSetMessage.objects.filter(id=msg_id)[0]
    project_id = new_item.message_set.project_id
    last_set = PotrSet.objects.filter(project_id=project_id).order_by('-id')[0]
    if PotrSetMessage.objects.filter(id=msg_id)[0].message_set == last_set:
        (PotrSetMessage.objects.filter(id=msg_id)
                               .update(msgstr=new_msg,
                                       is_translated=is_translated))
        for item in PotrSetMessage.objects.filter(id=msg_id):
            item.save()
    else:
        PotrSetMessage.objects.create(message_set=last_set,
                                      lang=new_item.lang,
                                      msgid=new_item.msgid,
                                      msgstr=new_msg,
                                      is_translated=is_translated)
    return {'saved': True}


@transaction.commit_on_success
def save_new(msg_id, new_msg):
    new_item = PotrSetMessage.objects.filter(id=msg_id)[0]
    msgid = new_item.msgid
    project_id = new_item.message_set.project_id.id
    last_set = PotrSet.objects.filter(project_id=project_id).order_by('-id')[0]
    obj, created = PotrSetMessage.objects.get_or_create(message_set=last_set,
                                       lang=new_item.lang,
                                       msgid=msgid)
    obj.msgstr = new_msg
    obj.is_translated = True
    obj.save()
    (PotrSetMessage.objects.filter(message_set=last_set.id, msgid=msgid)
                           .exclude(id=msg_id)
                           .update(is_translated=False))
    for lang in PotrProjectLanguage.objects.filter(
                            project_id=project_id).exclude(lang=new_item.lang):
        target_msg_kwargs = dict(msgid=msgid, lang=lang.lang)
        new_target, _ = PotrSetMessage.objects.get_or_create(
                                          message_set=last_set,
                                          defaults={'msgstr': new_msg,
                                                    'is_translated': False},
                                          **target_msg_kwargs)
        previous_msgs = (PotrSetMessage.objects
                                       .filter(**target_msg_kwargs)
                                       .exclude(id=msg_id)
                                       .order_by('-id'))
        if previous_msgs.count() > 1:
            new_target.msgstr = previous_msgs[1].msgstr
            new_target.save()
    return {'saved': True}


def show_prev(msg_id):
    message = PotrSetMessage.objects.get(id=msg_id)
    proj_id = message.message_set.project_id
    last_set = message.message_set
    lang = message.lang
    proj_lang = message.message_set.project_id.lang
    resp = {}

    for language, resp_field in [(proj_lang, 'prev_source'),
                                 (lang, 'prev_target')]:
        prev_value = (PotrSetMessage.objects
                                    .filter(msgid=message.msgid,
                                            message_set__project_id=proj_id,
                                            lang=language)
                                    .exclude(message_set=last_set)
                                    .order_by('-id'))
        prev_value = next(iter(prev_value), None)
        resp[resp_field] = (prev_value.msgstr if prev_value
                                                  else 'no information')
    return resp


def delete_last(project_id):
    """
    """
    if not PotrSet.objects.filter(project_id=project_id).count():
        return

    last_set = PotrSet.objects.filter(project_id=project_id).order_by('-id')[0]
    PotrSetMessage.objects.filter(message_set=last_set.id).delete()
    PotrSetList.objects.filter(message_set=last_set.id).delete()
    PotrImportMessage.objects.filter(
                                 import_id__message_set=last_set.id).delete()
    PotrImport.objects.filter(message_set=last_set.id).delete()
    PotrSet.objects.filter(id=last_set.id).delete()


def get_all_permissions(project_id):
    proj_langs = PotrProjectLanguage.objects.filter(project_id__id=project_id)
    result = []
    for lang in proj_langs:
        proj = PotrProjectLanguage.objects.get(project_id__id=project_id,
                                               lang=lang.lang.id)
        for user in User.objects.all():
            result.append(
                {'lang': lang.lang.name,
                'user': user.username,
                'can_change': user.has_perm('can_edit', proj)
                })
    return result

def user_has_perm(user_id, id_of_message):
    mes = PotrSetMessage.objects.get(id=id_of_message)
    proj = PotrProjectLanguage.objects.get(
                               project_id__id=mes.message_set.project_id.id,
                               lang=mes.lang.id)
    user = User.objects.get(id=user_id)
    if user.has_perm('can_edit', proj):
        return True
    else:
        return False
