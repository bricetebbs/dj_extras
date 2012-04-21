
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import subprocess

from django.db.models import get_app
from django.core.exceptions import *

class Command(BaseCommand):
    args = ''
    help = 'Load Compress mysql db into app'

    def handle(self, *args, **options):
        load_info = dict(username = settings.DATABASES['default']['USER'],
            password = settings.DATABASES['default']['USER'],
            db_name = settings.DATABASES['default']['NAME'],
            dump_path = settings.MYSQL_DUMP_ROOT)

        app_name_list= args
        for app_name in app_name_list:
            load_info['app_name'] = app_name
            try:
                app = get_app(app_name)
            except ImproperlyConfigured:
                raise CommandError('App "%s" does not exist' % app_name)
            cmd = "gunzip < %(dump_path)s%(app_name)s | mysql -u %(username)s -p%(password)s %(db_name)s" % load_info

            result = subprocess.check_call(cmd, shell=True)
            if result:
                raise CommandError("Load Failed")





