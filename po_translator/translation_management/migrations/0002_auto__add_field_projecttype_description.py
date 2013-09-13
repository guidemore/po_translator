# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ProjectType.description'
        db.add_column('potr_project_type', 'description',
                      self.gf('django.db.models.fields.CharField')(max_length=4000, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ProjectType.description'
        db.delete_column('potr_project_type', 'description')


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
            'description': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'null': 'True', 'blank': 'True'}),
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