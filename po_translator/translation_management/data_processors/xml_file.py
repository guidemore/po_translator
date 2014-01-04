from xml.etree import cElementTree

from . import base, data_processor_class, DataParsingError
from django.http import HttpResponse


@data_processor_class('xml_file')
class DataProcessor(base.DataProcessor):

    def parse_file(self, data_file):
        try:
            messages = cElementTree.fromstring(data_file)
        except Exception, e:
            raise DataParsingError(str(e))

        return ({"msgid": i.attrib['name'], "msgstr": i.text or ''} for i in messages.findall('.//string'))

    def export_file(self, dataset, language_code):
        messages_file = cElementTree.Element('resources')
        for row in dataset:
            string = cElementTree.SubElement(messages_file, 'string', {'name': row['msg_id']})
            string.text = row['msg_target']

        data = cElementTree.tostring(messages_file, encoding='UTF-8', method='xml')

        response = HttpResponse(data, mimetype='text/xml')
        response['Content-Disposition'] = 'attachment; filename="%s.xml"' % language_code

        return response
