import StringIO
import datetime
import zipfile
from django.core.files.base import ContentFile
from django.http import HttpResponse

import polib

from . import base, data_processor_class, DataParsingError


@data_processor_class('django')
class DataProcessor(base.DataProcessor):

    def parse_file(self, data_file):
        try:
            messages = polib.pofile(data_file)
        except Exception, e:
            raise DataParsingError(str(e))
        return ({"msgid": i.msgid, "msgstr": i.msgstr} for i in messages)

    def export_file(self, dataset, language_code):
        io = StringIO.StringIO()
        archive = zipfile.ZipFile(io, 'w')
        po = polib.POFile()

        po.metadata = {
            'Project-Id-Version': '1.0',
            'PO-Revision-Date': datetime.datetime.now(),
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit'
        }

        for row in dataset:
            entry = polib.POEntry(msgid=row['msg_id'], msgstr=row['msg_target'])
            po.append(entry)

        archive.writestr('locale/%s/LC_MESSAGES/django.po' % language_code, str(po))
        archive.writestr('locale/%s/LC_MESSAGES/django.mo' % language_code, po.to_binary())
        archive.close()
        io.seek(0)

        data = io.read()

        response = HttpResponse(data, mimetype='application/zip')
        response['Content-Disposition'] = 'attachment; filename="%s.zip"' % language_code

        return response
