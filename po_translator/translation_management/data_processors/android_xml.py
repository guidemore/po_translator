from . import base, data_processor_class, DataParsingError
from xml.etree import cElementTree as ET


@data_processor_class('android')
class DataProcessor(base.DataProcessor):
    def parse_file(self, data_file):
        try:
            messages = ET.fromstring(data_file)
        except Exception, e:
            raise DataParsingError(str(e))
        return ({"msgid": i.attrib['name'], "msgstr": i.text or ''} 
                 for i in messages.findall('.//string'))

    def export_file(self, dataset):

        messages_file = ET.Element('resources')
        for row in dataset:
            string = ET.SubElement(messages_file, 'string',
                                   {'name': row['msg_id']})
            string.text = row['msg_target']
        return ET.tostring(messages_file, encoding='utf8', method='xml')
