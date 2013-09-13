from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from . import models


class PotrImportAdmin(GuardedModelAdmin):
    pass


class PotrImportMessageAdmin(GuardedModelAdmin):
    pass


class PotrSetAdmin(GuardedModelAdmin):
    list_display = ('project_id', 'name', 'created_at')


class PotrSetListAdmin(GuardedModelAdmin):
    list_display = ('message_set', 'msgid', 'msgstr')


class PotrSetMessageAdmin(GuardedModelAdmin):
    pass

class PotrProjectAdmin(GuardedModelAdmin):
    pass


class ProjectTypeAdmin(GuardedModelAdmin):
    pass


class LanguageAdmin(GuardedModelAdmin):
    pass


class PotrProjectLanguageAdmin(GuardedModelAdmin):
    pass


admin.site.register(models.Language, LanguageAdmin)
admin.site.register(models.PotrImport, PotrImportAdmin)
admin.site.register(models.PotrImportMessage, PotrImportMessageAdmin)
admin.site.register(models.PotrProject, PotrProjectAdmin)
admin.site.register(models.PotrSet, PotrSetAdmin)
admin.site.register(models.PotrSetList, PotrSetListAdmin)
admin.site.register(models.PotrSetMessage, PotrSetMessageAdmin)
admin.site.register(models.ProjectType, ProjectTypeAdmin)
admin.site.register(models.PotrProjectLanguage, PotrProjectLanguageAdmin)
