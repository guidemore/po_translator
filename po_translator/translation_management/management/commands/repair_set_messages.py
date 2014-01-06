from django.core.management.base import BaseCommand, CommandError
from po_translator.translation_management.models import Project, Language, SetMessage
from po_translator.translation_management.utils import _update_message_query


class Command(BaseCommand):

    def handle(self, *args, **options):
        projects = Project.objects.all()
        for project in projects:
            messages = SetMessage.objects.all()
            sources = _update_message_query(messages, project.id, project.lang.id)

            project_languages = project.languages.all()
            for project_language in project_languages:
                if project_language.lang.id != project.lang_id:
                    language_messages = _update_message_query(messages, project.id, project_language.lang.id)
                    for message in language_messages:
                        if message.lang_id != project.lang_id:
                            for source in sources:
                                if source.msgid == message.msgid:
                                    message.source_message = source
                                    message.save()
