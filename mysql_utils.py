
from django.conf import settings

import subprocess

from django.db.models import get_app, get_models
from django.core.exceptions import *


def dump_mysql_db(app_name, tables = None, dump_path = None):

    if not dump_path:
        dump_path = "%s/%s.sql.gz" % (settings.MYSQL_DUMP_ROOT,app_name)

    dump_info = dict(username = settings.DATABASES['default']['USER'],
        password = settings.DATABASES['default']['USER'],
        db_name = settings.DATABASES['default']['NAME'],
        dump_path = dump_path,
        app_name = app_name)

    try:
        app = get_app(app_name)
    except ImproperlyConfigured:
        return dict(error='App "%s" does not exist' % app_name)

    if not tables:
        dump_info['tables'] = " ".join([x._meta.db_table for x in get_models(app, include_auto_created=True)])
    else:
        dump_info['tables'] = tables

    cmd = "mysqldump -u%(username)s -p%(password)s --skip-dump-date --skip-add-locks --no-create-info --opt  %(db_name)s %(tables)s  | gzip -n > %(dump_path)s" % dump_info

    print cmd
    result = subprocess.check_call(cmd, shell=True)
    if result:
        return dict(error="Dump Failed")

    return dict(error=None, dump_path=dump_info['dump_path'])
