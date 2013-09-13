from django.db import models
from django.db.models import signals


class ProjectType(models.Model):
    name = models.CharField(max_length=25)
    description = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        db_table = 'potr_project_type'

    def __unicode__(self):
        return u'%s' % (self.name)


class Language(models.Model):
    name = models.CharField(max_length=25)
    code = models.CharField(max_length=4)

    class Meta:
        db_table = 'potr_lang_type'

    def __unicode__(self):
        return u'%s' % (self.name)


class PotrProject(models.Model):
    name = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now=True)
    project_type = models.ForeignKey(ProjectType)
    lang = models.ForeignKey(Language)

    class Meta:
        db_table = 'potr_project'
        permissions = (('add_project', 'Add project'),)

    def __unicode__(self):
        return u'%s' % (self.name)


class PotrProjectLanguage(models.Model):
    lang = models.ForeignKey(Language)
    project_id = models.ForeignKey(PotrProject)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'potr_project_lang'
        permissions = (('can_edit', 'Edit message'),)

    def __unicode__(self):
        return u'%s:%s' % (self.project_id, self.lang_id)


class PotrSet(models.Model):
    project_id = models.ForeignKey(PotrProject)
    name = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'potr_set'
        permissions = (('add_set', 'Add set'),)

    def __unicode__(self):
        return u'%s' % (self.id)



class PotrSetMessage(models.Model):
    message_set = models.ForeignKey(PotrSet)
    lang = models.ForeignKey(Language)
    msgid = models.CharField(max_length=100)
    msgstr = models.CharField(max_length=4000)
    is_translated = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'potr_set_message'
        unique_together = ('msgid', 'message_set', 'lang')
        permissions = (('edit_message', 'Edit message'),)


    def __unicode__(self):
        return u'%s : %s' % (self.lang.name, self.msgid)

def add_other_languages_messages(sender, instance, created, **kwargs):
    project = instance.message_set.project_id
    if instance.lang_id != project.lang_id:
        return
    for lang in project.potrprojectlanguage_set.exclude(lang=instance.lang_id):
        PotrSetMessage.objects.get_or_create(
                                     message_set=instance.message_set,
                                     lang_id=lang.lang_id,
                                     msgid=instance.msgid,
                                     defaults={'is_translated':False,
                                               'msgstr': instance.msgstr})

signals.post_save.connect(add_other_languages_messages, sender=PotrSetMessage)


class PotrSetList(models.Model):
    message_set = models.ForeignKey(PotrSet)
    msgid = models.CharField(max_length=100)
    msgstr = models.CharField(max_length=4000)

    class Meta:
        db_table = 'potr_set_list'


class PotrImport(models.Model):
    message_set = models.ForeignKey(PotrSet)
    lang = models.ForeignKey(Language)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'potr_import'


class PotrImportMessage(models.Model):
    import_id = models.ForeignKey(PotrImport)
    msgid = models.CharField(max_length=100)
    msgstr = models.CharField(max_length=4000)

    class Meta:
        db_table = 'potr_import_message'

class PoFiles(models.Model):
    pofile = models.FileField(upload_to='documents/')


class ReadOnlyLastMessage(models.Model):
    message_set_id = models.IntegerField()
    lang_id = models.IntegerField()
    msgid = models.CharField(max_length=100)
    project_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'potr_latest_message_view'
