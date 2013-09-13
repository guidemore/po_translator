from django import forms
from models import (ProjectType, Language, Project, Set, SetMessage,
                    SetList, Import, ImportMessage, PoFiles,
                    ProjectLanguage)
from django.utils.translation import ugettext_lazy as _

from po_translator.translation_management import data_processors


class PoFileForm(forms.Form):
    lang = forms.ModelChoiceField(queryset=Language.objects.all(),
                                  empty_label=None,
                                  label=_('Select a language'))
    proj = forms.DecimalField()
    pofile = forms.FileField(label=_('Select a po-file'))


    def clean(self):
        cleaned_data = super(PoFileForm, self).clean()
        lang_id = cleaned_data.get('lang')
        project_id = int(cleaned_data.get('proj'))
        proj = Project.objects.get(id=project_id)
        if lang_id and project_id:
            lang_id = lang_id.id

            data_processor = data_processors.get_data_processor(proj.project_type.name)

            pofile = cleaned_data.get('pofile').read()
            try:
                translations_data = data_processor.parse_file(pofile)
            except data_processors.DataParsingError:
                if proj.project_type.description:
                    error = 'Error in file, %s' % proj.project_type.description
                else:
                    error = 'Error in file'
                raise forms.ValidationError(error)

            cleaned_data['pofile'] = pofile

            proj_lang = Project.objects.get(id=project_id).lang
            if lang_id in [x['lang'] for x in ProjectLanguage.objects.filter(project_id=project_id).values('lang').exclude(lang=proj_lang)]:
                raise forms.ValidationError(_('File with messages for this language already exist'))

            if lang_id == proj.lang_id:
                last_set = Set.objects.filter(project=project_id).order_by('-id')
                last_set = next(iter(last_set), None)
                all_messages = last_set and SetList.objects.filter(message_set=last_set) or []
                if set(i.msgid for i in all_messages) == set(i['msgid'] for i in translations_data):
                    raise forms.ValidationError(_('File with messages was not changed'))
            for entry in translations_data:
                if len(entry['msgid']) > 100:
                    raise forms.ValidationError(_('Too long msgid'))
                if len(entry['msgstr']) > 4000:
                    raise forms.ValidationError(_('Too long msgid'))

        return cleaned_data

    def clean_proj(self):
        proj = int(self.cleaned_data['proj'])
        if len(Project.objects.filter(id=proj)):
            return proj
        else:
            raise forms.ValidationError(_('Project does not exist'))



class MessageForm(forms.Form):
    id_of_message = forms.DecimalField()
    msg_str = forms.CharField(required=False, widget=forms.Textarea, max_length=4000)


class ProjectForm(forms.Form):
    name = forms.CharField(max_length=40)
    project_type = forms.ModelChoiceField(queryset=ProjectType.objects.all())
    lang = forms.ModelChoiceField(queryset=Language.objects.all())
    pofile = forms.FileField(required=True, label=_('Select a po-file'))

    def clean(self):
        cleaned_data = super(ProjectForm, self).clean()

        if not cleaned_data.get('pofile'):
            return None

        project_type = cleaned_data.get('project_type')
        data_processor = data_processors.get_data_processor(project_type.name)

        pofile = cleaned_data.get('pofile').read()
        try:
            translations_data = data_processor.parse_file(pofile)
        except data_processors.DataParsingError:
                if project_type.description:
                    error = 'Error in file, %s' % project_type.description
                else:
                    error = 'Error in file'
                raise forms.ValidationError(error)

        cleaned_data['pofile'] = pofile

        for entry in translations_data:
            if len(entry['msgid']) > 100:
                raise forms.ValidationError(_('Too long msgid'))
            if len(entry['msgstr']) > 4000:
                raise forms.ValidationError(_('Too long msgid'))
        return cleaned_data

class AddPermission(forms.Form):
    lang = forms.DecimalField()
    user = forms.DecimalField()
