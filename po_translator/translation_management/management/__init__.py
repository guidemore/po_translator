from django.db.models.signals import post_syncdb
from django.db import connection

from .. import models


def view_creation(sender, **kwargs):
    view_name = models.ReadOnlyLastMessage._meta.db_table
    if view_name in connection.introspection.table_names():
        return

    cursor = connection.cursor()
    cursor.execute("""CREATE VIEW {view_name} AS
                           SELECT NULL AS id,
                                  msgid,
                                  potr_set_message.lang_id as lang_id,
                                  Max(message_set_id) as message_set_id,
                                  potr_set.project_id_id as project_id
                             FROM potr_set_message
                             JOIN potr_set
                               ON potr_set.id=potr_set_message.message_set_id
                         GROUP BY project_id,
                                  msgid,
                                  lang_id;""".replace("\n", '')
                                             .format(view_name=view_name))

post_syncdb.connect(view_creation, sender=models)
