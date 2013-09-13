from abc import ABCMeta, abstractmethod


class DataProcessor:
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse_file(self, data_file):
        """
        receive translation file content
        return list of dictionaries (or generator)
        [
            {"msgid": msgid,
             "msgstr": msgstr},
            ...
        ]
        """
        pass

    @abstractmethod
    def export_file(self, dataset):
        """
        get list of dictionaries with message description
            {'msg_target': msg_target,
             'msg_source': msg_source,
             'is_translated': is_translated,
             'msg_id': msg_id,
             'target_id': target_id,
             'id': id}
        return string representation of file with translations
        """
        pass
