import csv
import cStringIO

from . import base, data_processor_class, DataParsingError


@data_processor_class('csv_file')
class DataProcessor(base.DataProcessor):
    def parse_file(self, data_file):
        try:
            messages = csv.reader(cStringIO.StringIO(data_file))
            fields = messages.next()
            name, value = fields[0], fields[1]
        except Exception, e:
            raise DataParsingError(str(e))
        return ({"msgid": i[0], "msgstr": i[1] or ''} for i in messages)

    def export_file(self, dataset, language_code=None):
        csvfile = cStringIO.StringIO()
        csv_writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        csv_writer.writerow(['msg_id', 'msg_target'])
        for row in dataset:
            csv_writer.writerow([row['msg_id'], row['msg_target']])
        return csvfile.getvalue()