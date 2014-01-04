import StringIO
import os
from unittest import TestCase
import zipfile

from django.test.client import Client
import polib
from django.contrib.auth.models import User

from po_translator.translation_management.models import (
    ProjectType, Language,
    Project, Set, SetMessage,
    SetList, Import,
    ImportMessage, ProjectLanguage)
from po_translator.translation_management.utils import (
    get_message_list, get_sections_info, get_all_permissions,
    import_po_file, save_same, save_same_target,
    save_new, show_prev, delete_last, user_has_perm)


# to register data processors import them
from po_translator.translation_management.data_processors import (po, csv_file, xml_file)

from guardian.shortcuts import assign_perm

PATH = os.path.dirname(__file__)


class TestUtils():
    def _get_po_file_from_zip(self, zip_content, language_code):
        zip_io = StringIO.StringIO(zip_content)
        zip_file = zipfile.ZipFile(zip_io, "r")
        po = polib.pofile(zip_file.read('locale/%s/LC_MESSAGES/django.po' % language_code))
        return po


class TestPoTranslate(TestCase):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2'}]
    target_messages = [{'message3': 'message3',
                        'message4': 'message4'}]

    def _setup_project(self, project_name, project_type, project_language):
        proj_type = ProjectType.objects.create(name=project_type)
        self.project_language, created = Language.objects.get_or_create(**project_language)
        self.project = Project.objects.create(name=project_name, project_type=proj_type, lang=self.project_language)
        ProjectLanguage.objects.create(lang=self.project_language, project=self.project)

    def setUp(self):
        self._setup_project('new_project', 'django', dict(name='English', code='en'))

        assert len(self.source_messages) == len(self.target_messages)
        self.new_lang = Language.objects.create(name='Russian', code='ru')
        ProjectLanguage.objects.create(lang=self.new_lang, project=self.project)

        for i, (source_data, target_data) in enumerate(zip(self.source_messages, self.target_messages)):
            potr_set = Set.objects.create(name='set_%d' % i, project=self.project)
            created_msgs = []
            for message_id, message in source_data.iteritems():
                _, created = SetMessage.objects.get_or_create(
                    lang=self.project_language,
                    msgid=message_id,
                    msgstr=message,
                    defaults={'message_set': potr_set, 'is_translated': True})
                if created:
                    created_msgs.append(message_id)
                SetList.objects.create(message_set=potr_set, msgid=message_id, msgstr=message)

            for message_id, message in target_data.iteritems():
                if message_id not in created_msgs:
                    continue
                target_message, _ = SetMessage.objects.get_or_create(
                    message_set=potr_set,
                    lang=self.new_lang,
                    msgid=message_id)
                target_message.msgstr = message
                target_message.is_translated = False
                target_message.save()

    def tearDown(self):
        Project.objects.all().delete()
        Language.objects.all().delete()
        ProjectType.objects.all().delete()
        SetMessage.objects.all().delete()
        Import.objects.all().delete()
        ImportMessage.objects.all().delete()
        SetList.objects.all().delete()
        Set.objects.all().delete()
        User.objects.all().delete()


class TestOneSetOneLang(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'}]
    target_messages = [{}]

    def test_get_message_list(self):
        mes = get_message_list(self.project.id, self.project_language.id)
        self.assertEqual(len(mes), 4)


class TestOneSetTwoLang(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'}]
    target_messages = [{'message1': 'message1_ru',
                        'message2': 'message2_ru'}]

    def test_get_message_list(self):
        mes = get_message_list(self.project.id, self.project_language.id)
        self.assertEqual(len(mes), 4)
        mes = get_message_list(self.project.id, self.new_lang.id)
        total_mes = sum(1 for row in mes if row['msg_target'])
        self.assertEqual(total_mes, 4)


class TestTwoSetWithDeletedItemOneLang(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'},
                       {'message1': 'message1',
                        'message2': 'message2'}]
    target_messages = [{}, {}]

    def test_get_message_list(self):
        mes = get_message_list(self.project.id, self.project_language.id)
        self.assertEqual(len(mes), 2)


class TestTwoSetWithDeletedItemTwoLang(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'},
                       {'message1': 'message1_new',
                        'message2': 'message2_new'}]
    target_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'},
                       {'message1': 'message1_new',
                        'message2': 'message2_new'}]

    def test_get_message_list(self):
        mes = get_message_list(self.project.id, self.project_language.id)
        self.assertEqual(len(mes), 2)
        mes = get_message_list(self.project.id, self.new_lang.id)
        self.assertEqual(len(mes), 2)


class TestTwoSetWithAddedItemOneLang(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'},
                       {'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4',
                        'message5': 'message5',
                        'message6': 'message6'}]
    target_messages = [{}, {}]

    def test_get_message_list(self):
        mes = get_message_list(self.project.id, self.project_language.id)
        self.assertEqual(len(mes), 6)


class TestTwoSetWithAddedItemTwoLang(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'},
                       {'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4',
                        'message5': 'message5',
                        'message6': 'message6'}]
    target_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'},
                       {'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3_ru',
                        'message4': 'message4',
                        'message5': 'message5',
                        'message6': 'message6_ru'}]

    def test_get_message_list(self):
        mes = get_message_list(self.project.id, self.project_language.id)
        self.assertEqual(len(mes), 6)
        mes = get_message_list(self.project.id, self.new_lang.id)
        self.assertEqual(len(mes), 6)


class TestSaveNewMeaning(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2'},
                       {'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3'}]
    target_messages = [{'message1': 'message1',
                        'message2': 'message2'},
                       {'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3'}]

    def test_save_new_meaning_new_set(self):
        last_set = Set.objects.all().order_by('-id')[0]
        message_to_edit = SetMessage.objects.get(
            message_set__project_id=self.project.id,
            msgid='message1',
            lang=self.project_language.id)

        new_value = 'message1 new'
        previous_set = message_to_edit.message_set
        last_set = self.project.set.order_by('-id')[0]
        response = save_new(message_to_edit.id, new_value)

        source_messages = SetMessage.objects.filter(
            message_set__project_id=self.project.id,
            msgid='message1',
            lang=self.project_language.id)
        self.assertEqual(source_messages.count(), 2)
        self.assertEqual(source_messages.order_by('-id')[1].message_set,
                         previous_set)
        self.assertEqual(source_messages.order_by('-id')[0].message_set, last_set)

        target_messages = SetMessage.objects.filter(
            message_set__project_id=self.project.id,
            msgid='message1',
            lang=self.new_lang)
        self.assertEqual(target_messages.count(), 2)
        self.assertEqual(target_messages.order_by('-id')[1].message_set, previous_set)
        self.assertEqual(target_messages.order_by('-id')[0].message_set, last_set)
        message_list = get_message_list(self.project.id, self.project_language.id)
        for mes in message_list:
            if mes['msg_id'] == message_to_edit.msgid:
                self.assertEqual(mes['msg_source'], new_value)
                break
            self.assertTrue(False)

        message_to_edit = mes
        new_value = 'message1 new1'
        response = save_new(message_to_edit['id'], new_value)
        message_list = get_message_list(self.project.id, self.project_language.id)
        for mes in message_list:
            if mes['msg_id'] == message_to_edit['msg_id']:
                self.assertEqual(mes['msg_source'], new_value)
                break
            self.assertTrue(False)
        message_to_edit = mes
        new_value = 'message1 new2'
        response = save_new(message_to_edit['id'], new_value)
        message_list = get_message_list(self.project.id, self.project_language.id)
        for mes in message_list:
            if mes['msg_id'] == message_to_edit['msg_id']:
                self.assertEqual(mes['msg_source'], new_value)
                break
            self.assertTrue(False)


class TestDeleteLastSet(TestPoTranslate):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message4': 'message4'},
                       {'message1': 'message1',
                        'message3': 'message3',
                        'message4': 'message4_new'}]
    target_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message4': 'message4'},
                       {'message1': 'message1',
                        'message3': 'message3',
                        'message4': 'message4_new'}]

    def test_delete_last_set(self):
        path = os.path.join(PATH, 'data/django.po')
        proj_type = ProjectType.objects.create(name='django')
        new_proj = Project.objects.create(name='Project2', project_type=proj_type, lang=self.project_language)
        import_po_file(path, new_proj.id, self.project_language.id)

        self.assertEqual(len(Set.objects.all()), 3)
        self.assertEqual(SetMessage.objects.filter(message_set__project_id=self.project.id).count(), 10)
        self.assertEqual(
            SetMessage.objects.filter(message_set__project_id=self.project.id, lang=self.project.lang).count(), 5)
        self.assertEqual(SetList.objects.filter(message_set__project_id=self.project.id).count(), 6)
        response = delete_last(self.project.id)

        self.assertEqual(len(Set.objects.all()), 2)

        self.assertEqual(SetMessage.objects.filter(message_set__project_id=self.project.id).count(), 6)
        self.assertEqual(
            SetMessage.objects.filter(message_set__project_id=self.project.id, lang=self.project.lang).count(), 3)
        self.assertEqual(SetList.objects.filter(
            message_set__project_id=self.project.id).count(), 3)

        response = delete_last(self.project.id)
        self.assertEqual(len(Set.objects.filter(project=self.project.id)), 0)
        self.assertEqual(SetList.objects.filter(
            message_set__project_id=self.project.id).count(), 0)
        self.assertEqual(len(Set.objects.all()), 1)


class TestFilterMessagesBySubstring(TestPoTranslate):
    source_messages = [{'mes.ssage1': 'messsage1',
                        'mess.age2': 'message2'},
                       {'mes.ssage1': 'messsage1',
                        'mess.age2': 'message2',
                        'mes.ssage3': 'message1',
                        'messs.age4': 'message4'}]
    target_messages = [{'mes.ssage1': 'massage1',
                        'mess.age2': 'message2'},
                       {'mes.ssage1': 'massage1',
                        'mess.age2': 'message2',
                        'mes.ssage3': 'messsaga3',
                        'messs.age4': 'message4'}]

    def test_import_source_lang(self):
        mes = get_message_list(self.project.id, self.new_lang.id,
                               src_filters={('msgid__contains',
                                             'msgstr__contains'): 'messs'})
        self.assertEqual(len(mes), 2)
        self.assertEqual(set(i['msg_id'] for i in mes), {'mes.ssage3', 'messs.age4'})

        mes = get_message_list(self.project.id, self.project_language.id,
                               src_filters={('msgid__contains',
                                             'msgstr__contains'): 'messs'})
        self.assertEqual(len(mes), 2)
        self.assertEqual(set(i['msg_id'] for i in mes), {'mes.ssage1', 'messs.age4'})


class TestDisplayDevs(TestPoTranslate, TestUtils):
    source_messages = [{'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'}]
    target_messages = [{}]

    def test_import_source_lang(self):
        path = os.path.join(PATH, 'data/django.po')
        import_po_file(path, self.project.id, self.project_language.id)
        self.assertEqual(len(ImportMessage.objects.all()), 10)
        self.assertEqual(len(Set.objects.all()), 2)

    def test_import_target_lang(self):
        path = os.path.join(PATH, 'data/django.po')
        new_lang = Language.objects.create(name='Russian', code='ru')
        ProjectLanguage.objects.create(lang=new_lang, project=self.project)
        import_po_file(path, self.project.id, new_lang.id)
        self.assertEqual(len(ImportMessage.objects.all()), 10)
        self.assertEqual(len(Set.objects.all()), 1)

    def test_import_source_lang_2(self):
        path = os.path.join(PATH, 'data/django.po')
        import_po_file(path, self.project.id, self.project_language.id)
        last_set = Set.objects.all().order_by('-id')[0]
        self.assertEqual(len(Set.objects.all()), 2)
        self.assertEqual(len(SetList.objects.filter(message_set=last_set)), 10)
        project_source_messages = SetMessage.objects.filter(message_set__project_id=self.project.id)
        self.assertEqual(project_source_messages.filter(lang=self.project.lang).count(), 14)
        self.assertEqual(project_source_messages.filter(
            lang=self.project.lang,
            message_set=last_set).count(), 10)
        for i in project_source_messages.filter(lang=self.project.lang, message_set=last_set):
            self.assertTrue(i.is_translated)

    def test_import_source_lang_with_two_lang(self):
        path = os.path.join(PATH, 'data/django.po')
        new_lang = Language.objects.create(name='Russian', code='ru')
        ProjectLanguage.objects.create(lang=new_lang, project=self.project)
        import_po_file(path, self.project.id, self.project_language.id)
        self.assertEqual(len(Set.objects.all()), 2)
        last_set = Set.objects.all().order_by('-id')[0]
        self.assertEqual(
            len(SetMessage.objects.filter(
                message_set__project_id=self.project.id, lang=new_lang.id)), 10)
        for i in SetMessage.objects.filter(
                message_set__project_id=self.project.id,
                message_set=last_set,
                lang=new_lang.id):
            self.assertFalse(i.is_translated)
            self.assertTrue(len(i.msgstr) > 0)

    def test_double_import_source_lang(self):
        path = os.path.join(PATH, 'data/django1.po')
        import_po_file(path, self.project.id, self.project_language.id)
        import_po_file(path, self.project.id, self.project_language.id)
        last_set = Set.objects.all().order_by('-id')[0]
        #TODO: need asser error!!!

    def test_import_export_android_file(self):
        from xml.etree import ElementTree as ET

        self._setup_project('android_project', 'xml_file', dict(name='English', code='en'))
        path = os.path.join(PATH, 'data/android.xml')
        with open(path, 'r') as data_file:
            import_po_file(data_file.read(), self.project.id, self.project_language.id)
        last_set = Set.objects.all().order_by('-id')[0]
        self.assertEqual(len(ImportMessage.objects.all()), 5)
        self.assertEqual(len(Set.objects.all()), 2)
        client = Client()
        user = User.objects.create(username='Admin')
        user.set_password('Admin')
        user.save()
        client.login(username='Admin', password='Admin')
        response = client.get('/project/%s/export/%s/' % (self.project.id, self.project_language.id))
        messages = [{"msgid": i.attrib['name'], "msgstr": i.text or ''}
                    for i in ET.fromstring(response.content).findall('.//string')]
        self.assertEqual(len(messages), 5)
        mess_keys = [k['msgid'] for k in messages]
        for msg in SetMessage.objects.filter(message_set=last_set):
            self.assertTrue(msg.msgid in mess_keys)

    def test_import_export_csv_file(self):
        import csv
        import cStringIO

        self._setup_project('csv_project', 'csv_file', dict(name='English', code='en'))
        path = os.path.join(PATH, 'data/csv.csv')
        with open(path, 'r') as data_file:
            import_po_file(data_file.read(), self.project.id, self.project_language.id)
        last_set = Set.objects.all().order_by('-id')[0]
        self.assertEqual(len(ImportMessage.objects.all()), 5)
        self.assertEqual(len(Set.objects.all()), 2)
        client = Client()
        user = User.objects.create(username='Admin')
        user.set_password('Admin')
        user.save()
        client.login(username='Admin', password='Admin')
        response = client.get('/project/%s/export/%s/' % (self.project.id,
                                                          self.project_language.id))
        messages = csv.reader(cStringIO.StringIO(response.content))
        fields = messages.next()
        messages = [{"msgid": i[0], "msgstr": i[1] or ''} for i in messages]

        self.assertEqual(len(messages), 5)
        mess_keys = [k['msgid'] for k in messages]
        for msg in SetMessage.objects.filter(message_set=last_set):
            self.assertTrue(msg.msgid in mess_keys)

    def test_import_source_new_lang_with_two_lang(self):
        path = os.path.join(PATH, 'data/django.po')
        import_po_file(path, self.project.id, self.project_language.id)
        self.assertEqual(len(Set.objects.all()), 2)
        new_lang = Language.objects.create(name='Russian', code='ru')
        ProjectLanguage.objects.create(lang=new_lang, project=self.project)
        last_set = Set.objects.all().order_by('-id')[0]
        path = os.path.join(PATH, 'data/django_ru.po')
        import_po_file(path, self.project.id, new_lang.id)

        self.assertEqual(last_set.id, Set.objects.all().order_by('-id')[0].id)
        self.assertEqual(len(SetMessage.objects.filter( message_set__project_id=self.project.id, lang=new_lang.id)), 10)
        for i in SetMessage.objects.filter(
                message_set__project_id=self.project.id,
                message_set=last_set, lang=new_lang.id):
            self.assertFalse(i.is_translated)
            self.assertTrue(len(i.msgstr) > 0)

    def test_export_po_file_with_two_lang_check_record_number(self):
        client = Client()
        user = User.objects.create(username='Admin')
        user.set_password('Admin')
        user.save()
        client.login(username='Admin', password='Admin')

        response = client.get('/project/%s/export/%s/' % (self.project.id, self.project_language.id))
        self.assertEqual(response.status_code, 200)
        po = self._get_po_file_from_zip(response.content, self.project_language.code)

        self.assertEqual(
            len(SetMessage.objects.filter(message_set__project_id=self.project.id, lang=self.project_language.id)),
            len(po.translated_entries()))

        new_lang = Language.objects.create(name='Russian', code='ru')
        new_project_language = ProjectLanguage.objects.create(lang=new_lang, project=self.project)
        path = os.path.join(PATH, 'data/django.po')
        import_po_file(path, self.project.id, self.project_language.id)

        response = client.get('/project/%s/export/%s/' % (self.project.id, new_lang.id))
        po = self._get_po_file_from_zip(response.content, new_lang.code)
        all_messages = SetMessage.objects.filter(message_set__project_id=self.project.id, lang=new_lang.id)

        self.assertEqual(len(all_messages), len(po.translated_entries()))
        self.assertTrue(
            dict((i.msgid, unicode(i.msgstr, 'utf8')) for i in po) == dict((i.msgid, i.msgstr) for i in all_messages))
        self.assertTrue(set(i.msgid for i in all_messages) == set(i.msgid for i in po))

    def test_export_po_file_with_empty_msgstr_in_target_lang(self):
        client = Client()
        user = User.objects.create(username='Admin')
        user.set_password('Admin')
        user.save()
        client.login(username='Admin', password='Admin')

        new_lang = Language.objects.create(name='Japan', code='jp')
        ProjectLanguage.objects.create(lang=new_lang, project=self.project)
        path = os.path.join(PATH, 'data/django1.po')
        import_po_file(path, self.project.id, self.project_language.id)
        SetMessage.objects.filter(msgid='test.empty', lang=self.project.lang.id).update(msgstr='NonEmpty')
        response = client.get('/project/%s/export/%s/' % (self.project.id, new_lang.id))
        po = self._get_po_file_from_zip(response.content, new_lang.code)
        all_messages = SetMessage.objects.filter(message_set__project_id=self.project.id, lang=self.project.lang.id)
        self.assertFalse(SetMessage.objects.get(msgid='test.empty', lang=new_lang.id).msgstr)
        self.assertEqual(dict((i.msgid, unicode(i.msgstr, 'utf8')) for i in po)['test.empty'], 'NonEmpty')

        SetMessage.objects.filter(msgid='test.empty').update(is_translated=True)
        response = client.get('/project/%s/export/%s/' % (self.project.id, new_lang.id))
        po = self._get_po_file_from_zip(response.content, new_lang.code)
        all_messages = SetMessage.objects.filter(message_set__project_id=self.project.id, lang=self.project.lang.id)
        self.assertFalse(SetMessage.objects.get(msgid='test.empty', lang=new_lang.id).msgstr)
        self.assertFalse(dict((i.msgid, unicode(i.msgstr, 'utf8')) for i in po)['test.empty'])

    def test_save_same_meaning(self):
        last_set = Set.objects.all().order_by('-id')[0]
        message_to_edit = SetMessage.objects.filter(
            message_set__project_id=self.project.id,
            lang=self.project_language.id,
            message_set=last_set)[0]
        new_value = 'test'
        response = save_same(message_to_edit.id, new_value)
        self.assertEqual(SetMessage.objects.filter(id=message_to_edit.id)[0].msgstr, new_value)

    def test_save_new_meaning(self):
        last_set = Set.objects.all().order_by('-id')[0]
        message_to_edit = SetMessage.objects.filter(
            message_set__project_id=self.project.id,
            lang=self.project_language.id,
            message_set=last_set)[0]
        new_value = 'test'
        new_lang = Language.objects.create(name='Russian', code='ru')
        new_lang_2 = Language.objects.create(name='Spanish', code='sp')
        ProjectLanguage.objects.create(lang=new_lang, project=self.project)
        ProjectLanguage.objects.create(lang=new_lang_2, project=self.project)
        for item in SetMessage.objects.filter(lang=self.project_language.id):
            SetMessage.objects.create(
                message_set=item.message_set,
                lang=new_lang,
                msgid=item.msgid,
                msgstr=item.msgstr,
                is_translated=True
            )
        response = save_new(message_to_edit.id, new_value)
        self.assertEqual(SetMessage.objects.filter(
            msgid=message_to_edit.msgid,
            lang=message_to_edit.lang
        ).order_by('-id')[0].msgstr, new_value)
        self.assertEqual(SetMessage.objects.filter(
            msgid=message_to_edit.msgid
        ).order_by('-id')[0].message_set, last_set)
        self.assertFalse(SetMessage.objects.filter(
            msgid=message_to_edit.msgid,
            lang=new_lang)[0].is_translated)
        self.assertFalse(SetMessage.objects.filter(
            msgid=message_to_edit.msgid,
            lang=new_lang_2)[0].is_translated)

    def test_save_same_meaning_target(self):
        last_set = Set.objects.all().order_by('-id')[0]
        message_to_edit = SetMessage.objects.filter(
            message_set__project_id=self.project.id,
            lang=self.project_language.id,
            message_set=last_set)[0]
        new_value = 'test'
        response = save_same_target(message_to_edit.id, new_value, u"True")
        self.assertEqual(SetMessage.objects.filter(
            id=message_to_edit.id)[0].msgstr, new_value)
        self.assertTrue(SetMessage.objects.filter(
            id=message_to_edit.id)[0].is_translated)
        response = save_same_target(message_to_edit.id, new_value, u"False")
        self.assertFalse(SetMessage.objects.filter(
            id=message_to_edit.id)[0].is_translated)

    def test_show_prev(self):
        path = os.path.join(PATH, 'data/django.po')
        new_lang = Language.objects.create(name='Russian', code='ru')
        ProjectLanguage.objects.create(lang=new_lang, project=self.project)
        import_po_file(path, self.project.id, self.project_language.id)
        last_set = Set.objects.all().order_by('-id')[0]
        message_to_edit = SetMessage.objects.filter(lang=self.project_language.id,
                                                    message_set=last_set,
                                                    msgid='Submitted')[0]
        path = os.path.join(PATH, 'data/django1.po')
        import_po_file(path, self.project.id, self.project_language.id)
        new_value = 'test'
        response = save_new(message_to_edit.id, new_value)

        last_set = Set.objects.all().order_by('-id')[0]
        message_to_edit2 = SetMessage.objects.filter(
            lang=new_lang.id,
            message_set=last_set,
            msgid=message_to_edit.msgid)[0]
        response = show_prev(message_to_edit2.id)
        self.assertEqual(response['prev_source'], message_to_edit.msgstr)
        self.assertEqual(response['prev_target'], message_to_edit.msgstr)

    def test_potr_proj_lang(self):
        path = os.path.join(PATH, 'data/django.po')
        proj_type = ProjectType.objects.create(name='django')
        proj_lang_2 = Language.objects.create(name='Russian', code='ru')
        proj_2 = Project.objects.create(name='Project1',
                                        project_type=proj_type,
                                        lang=proj_lang_2)
        potr_set_2 = Set.objects.create(name='initial', project=proj_2)
        ProjectLanguage.objects.create(lang=proj_lang_2, project=proj_2)

        for message in ['message1', 'message2', 'message3', 'message4']:
            SetMessage.objects.create(
                message_set=potr_set_2,
                lang=proj_lang_2,
                msgid=message[-3:],
                msgstr=message,
                is_translated=False
            )
            SetList.objects.create(
                message_set=potr_set_2,
                msgid=message[-3:],
                msgstr=message)
        mes = get_message_list(self.project.id, self.project_language.id)
        self.assertEqual(len(mes), 4)
        mes = get_message_list(proj_2.id, proj_lang_2.id)
        self.assertEqual(len(mes), 4)
        import_po_file(path, self.project.id, self.project_language.id)
        self.assertEqual(SetMessage.objects.filter(
            message_set__project_id=self.project.id,
            lang__id=proj_lang_2.id).count(), 0)


class TestMultiProjectPoTranslate(TestPoTranslate):
    source_messages = [{'mes.sag.e1': 'message1', 'mes.sag.e2': 'message2'}]
    target_messages = [{'mes.sag.e1': 'message1', 'mes.sag.e2': 'message2'}]
    new_source_messages = source_messages
    new_target_messages = target_messages

    def setUp(self):
        super(TestMultiProjectPoTranslate, self).setUp()
        self.new_project = self._add_project()
        self._add_message(self.new_project)

    def _add_project(self, project_name='new_project'):
        proj_type = ProjectType.objects.all()[0]
        new_proj = Project.objects.create(name='proj_2', project_type=proj_type, lang=self.project_language)
        ProjectLanguage.objects.create(lang=self.project_language, project=new_proj)
        return new_proj

    def _add_message(self, new_proj):
        for i, (source_data, target_data) in enumerate(zip(self.new_source_messages, self.new_target_messages)):
            potr_set = Set.objects.create(name='set_%d' % i, project=new_proj)
            created_msgs = []
            for message_id, message in source_data.iteritems():
                _, created = SetMessage.objects.get_or_create(
                    lang=self.project_language,
                    msgid=message_id,
                    msgstr=message,
                    message_set__project_id=new_proj,
                    defaults={'message_set': potr_set,
                              'is_translated': True})
                if created:
                    created_msgs.append(message_id)
                SetList.objects.create(message_set=potr_set,
                                       msgid=message_id,
                                       msgstr=message)
            for message_id, message in target_data.iteritems():
                if message_id not in created_msgs:
                    continue
                target_message, _ = SetMessage.objects.get_or_create(
                    message_set=potr_set,
                    lang=self.new_lang,
                    msgid=message_id)
                target_message.msgstr = message
                target_message.is_translated = False
                target_message.save()


class TestChangeValue(TestMultiProjectPoTranslate):
    def test_change_value_in_one_project(self):
        message_to_edit = SetMessage.objects.get(
            message_set__project_id=self.project.id,
            msgid='mes.sag.e1',
            lang=self.project_language.id)
        source_messages = SetMessage.objects.filter(
            msgstr='message1',
            lang=self.project_language.id)
        self.assertEqual(source_messages.count(), 2)
        new_value = 'message1 new'
        response = save_same(message_to_edit.id, new_value)
        source_messages = SetMessage.objects.filter(
            msgstr='message1 new',
            lang=self.project_language.id)
        self.assertEqual(source_messages.count(), 1)

    def test_change_value_after_import_in_one_project(self):
        path = os.path.join(PATH, 'data/mess.po')
        source_messages = SetMessage.objects.filter(
            msgstr='message1',
            lang=self.project_language.id)
        self.assertEqual(source_messages.count(), 2)

        import_po_file(path, self.project.id, self.project_language.id)
        import_po_file(path, self.new_project.id, self.project_language.id)
        source_messages = SetMessage.objects.filter(
            msgstr='title_title',
            lang=self.project_language.id)
        self.assertEqual(source_messages.count(), 2)
        message_to_edit = SetMessage.objects.get(
            message_set__project_id=self.project.id,
            msgid='1.Title',
            lang=self.project_language.id)

        #Check same meaning update
        new_value = 'message1 new'
        response = save_same(message_to_edit.id, new_value)
        source_messages = SetMessage.objects.filter(
            msgstr='message1 new',
            lang=self.project_language.id)
        self.assertEqual(source_messages.count(), 1)

        first_mes = get_message_list(self.project.id, self.project_language.id)
        second_mes = get_message_list(self.new_project.id, self.project_language.id)

        src_msg_list = {i['msg_id']: i['msg_source'] for i in first_mes}
        self.assertEqual(src_msg_list['1.Title'], 'message1 new')

        src_msg_list = {i['msg_id']: i['msg_source'] for i in second_mes}
        self.assertEqual(src_msg_list['1.Title'], 'title_title')

        #Check new meaning update
        new_value = 'message1 new2'
        response = save_new(message_to_edit.id, new_value)
        source_messages = SetMessage.objects.filter(
            msgstr='message1 new2',
            lang=self.project_language.id)
        self.assertEqual(source_messages.count(), 1)
        first_mes = get_message_list(self.project.id, self.project_language.id)
        second_mes = get_message_list(self.new_project.id, self.project_language.id)

        src_msg_list = {i['msg_id']: i['msg_source'] for i in first_mes}
        self.assertEqual(src_msg_list['1.Title'], 'message1 new2')

        src_msg_list = {i['msg_id']: i['msg_source'] for i in second_mes}
        self.assertEqual(src_msg_list['1.Title'], 'title_title')


class TestSectionTwoProjects(TestMultiProjectPoTranslate):
    source_messages = [{'mes.sag.e1': 'message1',
                        'mes.sag.e2': 'message2'}]
    target_messages = [{'mes.sag.e1': 'message1',
                        'mes.sag.e2': 'message2'}]
    new_source_messages = [{'mess.ag.e1': 'message1',
                            'mes.sage.2': 'message2'}]
    new_target_messages = [{'mess.ag.e1': 'message1',
                            'mes.sage.2': 'message2'}]

    def test_sections(self):
        sect, subsect = get_sections_info(self.project.id, self.project_language.id)
        self.assertEqual(sect, ['mes'])
        sect, subsect = get_sections_info(self.new_project.id,
                                          self.project_language.id)
        self.assertEqual(sect, ['mes', 'mess'])

    def test_subsections(self):
        section_filters = {}
        section_filters['msgid__startswith'] = 'mes.'
        sect, subsect = get_sections_info(self.project.id, self.project_language.id,
                                          section_filters=section_filters)
        self.assertEqual(subsect, ['sag'])
        section_filters['msgid__startswith'] = 'mes.'
        sect, subsect = get_sections_info(self.new_project.id,
                                          self.project_language.id,
                                          section_filters=section_filters)
        self.assertEqual(subsect, ['sage'])


class TestPermissions(TestMultiProjectPoTranslate):
    def setUp(self):
        super(TestPermissions, self).setUp()

        for username in ['admin', 'user1', 'user2']:
            user = User.objects.create(username=username)
        self.user = User.objects.get(username='admin')
        for lang in ProjectLanguage.objects.all():
            proj = ProjectLanguage.objects.get(project_id=self.project.id, lang=lang.lang)
            assign_perm('can_read', self.user, proj)
        self.user2 = User.objects.get(username='user2')
        for lang in ProjectLanguage.objects.all():
            proj = ProjectLanguage.objects.get(project_id=self.project.id, lang=lang.lang)
            assign_perm('can_edit', self.user2, proj)


class TestPermissionPoTrans(TestPermissions):
    def test_list_with_perms(self):
        perms = get_all_permissions(self.project.id)
        for row in perms:
            if row['user'] == self.user.username:
                self.assertTrue(row['can_read'])
            else:
                self.assertFalse(row['can_read'])
        for row in perms:
            if row['user'] == self.user2.username:
                self.assertTrue(row['can_change'])
            else:
                self.assertFalse(row['can_change'])


    def test_check_perms(self):
        last_set = Set.objects.filter(
            project_id=self.project.id).order_by('-id')[0]
        message_to_edit = SetMessage.objects.filter(lang=self.project_language.id,
                                                    message_set=last_set)[0]
        self.assertTrue(user_has_perm(self.user2.id, message_to_edit.id))
        user1 = User.objects.get(username='user1')
        self.assertFalse(user_has_perm(user1.id, message_to_edit.id))


class TestExportPoFile(TestPoTranslate, TestUtils):
    source_messages = [{'message1': 'message1_old',
                        'message3': 'message3',
                        'message5': 'message5',
                        'message4': 'message4_old'},
                       {'message1': 'message1',
                        'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'}]
    target_messages = [{'message1': 'ru_message1_old',
                        'message3': 'ru_message3',
                        'message5': 'ru_message5',
                        'message4': 'ru_message4_old'},
                       {'message1': 'ru_message1',
                        'message2': 'ru_message2',
                        'message3': 'ru_message3',
                        'message4': 'ru_message4'}]

    def test_export_po_file_with_two_lang_check_records(self):
        client = Client()
        user = User.objects.create(username='Admin')
        user.set_password('Admin')
        user.save()
        SetMessage.objects.all().update(is_translated=True)
        client.login(username='Admin', password='Admin')

        response = client.get('/project/%s/export/%s/' % (self.project.id, self.project_language.id))
        self.assertEqual(response.status_code, 200)
        src_po = self._get_po_file_from_zip(response.content, self.project_language.code)
        response = client.get('/project/%s/export/%s/' % (self.project.id, self.new_lang.id))
        target_po = self._get_po_file_from_zip(response.content, self.new_lang.code)
        src_msgs = {i.msgid: i.msgstr for i in src_po.translated_entries()}
        self.assertEqual(src_msgs, self.source_messages[-1])
        new_msgs = {i.msgid: i.msgstr for i in target_po.translated_entries()}
        self.assertEqual(new_msgs, self.target_messages[-1])


class TestSaveNewMeaningSimple(TestPoTranslate):
    source_messages = [{'message3': 'message3',
                        'message5': 'message5',
                        'message4': 'message4_old'},
                       {'message2': 'message2',
                        'message3': 'message3',
                        'message4': 'message4'}]
    target_messages = [{'message3': 'ru_message3',
                        'message5': 'ru_message5',
                        'message4': 'ru_message4_old'},
                       {'message2': 'ru_message2',
                        'message3': 'ru_message3',
                        'message4': 'ru_message4'}]

    def test_save_new_meaning_for_old_set_message(self):
        messages = SetMessage.objects.filter(
            message_set__project_id=self.project.id,
            msgid='message3')
        src_message_versions = messages.filter(lang=self.project_language.id)
        self.assertEqual(messages.count(), 2)
        self.assertEqual(src_message_versions.count(), 1)
        new_value = 'message3_new'
        response = save_new(src_message_versions[0].id, new_value)
        self.assertTrue(response['saved'])
        self.assertEqual(messages.all().count(), 4)
        target_message_versions = messages.filter(lang=self.new_lang.id)
        self.assertEqual(target_message_versions.count(), 2)
        self.assertEqual(set(i.msgstr for i in target_message_versions), set(['ru_message3']))
