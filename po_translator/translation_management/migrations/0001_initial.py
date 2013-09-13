# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ProjectType'
        db.create_table('potr_project_type', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=25)),
        ))
        db.send_create_signal(u'translation_management', ['ProjectType'])

        # Adding model 'Language'
        db.create_table('potr_lang_type', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=4)),
        ))
        db.send_create_signal(u'translation_management', ['Language'])

        # Adding model 'Project'
        db.create_table('potr_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('project_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.ProjectType'])),
            ('lang', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Language'])),
        ))
        db.send_create_signal(u'translation_management', ['Project'])

        # Adding model 'ProjectLanguage'
        db.create_table('potr_project_lang', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lang', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Language'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Project'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'translation_management', ['ProjectLanguage'])

        # Adding model 'Set'
        db.create_table('potr_set', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Project'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'translation_management', ['Set'])

        # Adding model 'SetMessage'
        db.create_table('potr_set_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Set'])),
            ('lang', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Language'])),
            ('msgid', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('msgstr', self.gf('django.db.models.fields.CharField')(max_length=4000)),
            ('is_translated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'translation_management', ['SetMessage'])

        # Adding unique constraint on 'SetMessage', fields ['msgid', 'message_set', 'lang']
        db.create_unique('potr_set_message', ['msgid', 'message_set_id', 'lang_id'])

        # Adding model 'SetList'
        db.create_table('potr_set_list', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Set'])),
            ('msgid', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('msgstr', self.gf('django.db.models.fields.CharField')(max_length=4000)),
        ))
        db.send_create_signal(u'translation_management', ['SetList'])

        # Adding model 'Import'
        db.create_table('potr_import', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Set'])),
            ('lang', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Language'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'translation_management', ['Import'])

        # Adding model 'ImportMessage'
        db.create_table('potr_import_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poimport', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translation_management.Import'])),
            ('msgid', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('msgstr', self.gf('django.db.models.fields.CharField')(max_length=4000)),
        ))
        db.send_create_signal(u'translation_management', ['ImportMessage'])

        # Adding model 'PoFiles'
        db.create_table(u'translation_management_pofiles', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pofile', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal(u'translation_management', ['PoFiles'])


    def backwards(self, orm):
        # Removing unique constraint on 'SetMessage', fields ['msgid', 'message_set', 'lang']
        db.delete_unique('potr_set_message', ['msgid', 'message_set_id', 'lang_id'])

        # Deleting model 'ProjectType'
        db.delete_table('potr_project_type')

        # Deleting model 'Language'
        db.delete_table('potr_lang_type')

        # Deleting model 'Project'
        db.delete_table('potr_project')

        # Deleting model 'ProjectLanguage'
        db.delete_table('potr_project_lang')

        # Deleting model 'Set'
        db.delete_table('potr_set')

        # Deleting model 'SetMessage'
        db.delete_table('potr_set_message')

        # Deleting model 'SetList'
        db.delete_table('potr_set_list')

        # Deleting model 'Import'
        db.delete_table('potr_import')

        # Deleting model 'ImportMessage'
        db.delete_table('potr_import_message')

        # Deleting model 'PoFiles'
        db.delete_table(u'translation_management_pofiles')


    models = {
        u'translation_management.language': {
            'Meta': {'object_name': 'Language', 'db_table': "'potr_lang_type'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        u'translation_management.pofiles': {
            'Meta': {'object_name': 'PoFiles'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pofile': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        u'translation_management.potrimport': {
            'Meta': {'object_name': 'Import', 'db_table': "'potr_import'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Language']"}),
            'message_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Set']"})
        },
        u'translation_management.potrimportmessage': {
            'Meta': {'object_name': 'ImportMessage', 'db_table': "'potr_import_message'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poimport': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Import']"}),
            'msgid': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'msgstr': ('django.db.models.fields.CharField', [], {'max_length': '4000'})
        },
        u'translation_management.potrproject': {
            'Meta': {'object_name': 'Project', 'db_table': "'potr_project'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Language']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'project_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.ProjectType']"})
        },
        u'translation_management.potrprojectlanguage': {
            'Meta': {'object_name': 'ProjectLanguage', 'db_table': "'potr_project_lang'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Language']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Project']"})
        },
        u'translation_management.potrset': {
            'Meta': {'object_name': 'Set', 'db_table': "'potr_set'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Project']"})
        },
        u'translation_management.potrsetlist': {
            'Meta': {'object_name': 'SetList', 'db_table': "'potr_set_list'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Set']"}),
            'msgid': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'msgstr': ('django.db.models.fields.CharField', [], {'max_length': '4000'})
        },
        u'translation_management.potrsetmessage': {
            'Meta': {'unique_together': "(('msgid', 'message_set', 'lang'),)", 'object_name': 'SetMessage', 'db_table': "'potr_set_message'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_translated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lang': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Language']"}),
            'message_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translation_management.Set']"}),
            'msgid': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'msgstr': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'translation_management.projecttype': {
            'Meta': {'object_name': 'ProjectType', 'db_table': "'potr_project_type'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        u'translation_management.readonlylastmessage': {
            'Meta': {'object_name': 'ReadOnlyLastMessage', 'db_table': "'potr_latest_message_view'", 'managed': 'False'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang_id': ('django.db.models.fields.IntegerField', [], {}),
            'message_set_id': ('django.db.models.fields.IntegerField', [], {}),
            'msgid': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'project_id': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['translation_management']