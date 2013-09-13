from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from . import models


class ImportAdmin(GuardedModelAdmin):
    pass


class ImportMessageAdmin(GuardedModelAdmin):
    pass


class SetAdmin(GuardedModelAdmin):
    list_display = ('project', 'name', 'created_at')


class SetListAdmin(GuardedModelAdmin):
    list_display = ('message_set', 'msgid', 'msgstr')


class SetMessageAdmin(GuardedModelAdmin):
    pass


class ProjectAdmin(GuardedModelAdmin):
    pass


class ProjectTypeAdmin(GuardedModelAdmin):
    pass


class LanguageAdmin(GuardedModelAdmin):
    pass


class ProjectLanguageAdmin(GuardedModelAdmin):
    pass


admin.site.register(models.Language, LanguageAdmin)
admin.site.register(models.Import, ImportAdmin)
admin.site.register(models.ImportMessage, ImportMessageAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Set, SetAdmin)
admin.site.register(models.SetList, SetListAdmin)
admin.site.register(models.SetMessage, SetMessageAdmin)
admin.site.register(models.ProjectType, ProjectTypeAdmin)
admin.site.register(models.ProjectLanguage, ProjectLanguageAdmin)
