from django.db import models
from django.db.models import signals


class ProjectType(models.Model):
    name = models.CharField(max_length=25)
    description = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        db_table = 'potr_project_type'

    def __unicode__(self):
        return u'%s' % self.name


class Language(models.Model):
    name = models.CharField(max_length=25)
    code = models.CharField(max_length=4)

    class Meta:
        db_table = 'potr_lang_type'

    def __unicode__(self):
        return u'%s' % self.name


class Project(models.Model):
    name = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now=True)
    project_type = models.ForeignKey(ProjectType)
    lang = models.ForeignKey(Language)

    class Meta:
        db_table = 'potr_project'

    def __unicode__(self):
        return u'%s' % self.name


class ProjectLanguage(models.Model):
    lang = models.ForeignKey(Language)
    project = models.ForeignKey(Project, related_name='languages')
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'potr_project_lang'
        permissions = (('can_edit', 'Edit message'),
                       ('can_read', 'Read message'),)

    def __unicode__(self):
        return u'%s:%s' % (self.project, self.lang_id)


class Set(models.Model):
    project = models.ForeignKey(Project, related_name='set')
    name = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'potr_set'

    def __unicode__(self):
        return u'%s' % self.id


class SetMessage(models.Model):
    message_set = models.ForeignKey(Set)
    lang = models.ForeignKey(Language)
    source_message = models.ForeignKey('self', null=True, blank=True)
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
    project = instance.message_set.project
    if instance.lang_id != project.lang_id:
        return

    for lang in project.languages.exclude(lang=instance.lang_id):
        SetMessage.objects.get_or_create(
            message_set=instance.message_set,
            lang_id=lang.lang_id,
            msgid=instance.msgid,
            defaults={'is_translated': False, 'msgstr': instance.msgstr, 'source_message': instance}
        )


signals.post_save.connect(add_other_languages_messages, sender=SetMessage)


class SetList(models.Model):
    message_set = models.ForeignKey(Set)
    msgid = models.CharField(max_length=100)
    msgstr = models.CharField(max_length=4000)

    class Meta:
        db_table = 'potr_set_list'


class Import(models.Model):
    message_set = models.ForeignKey(Set)
    lang = models.ForeignKey(Language)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'potr_import'


class ImportMessage(models.Model):
    poimport = models.ForeignKey(Import)
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