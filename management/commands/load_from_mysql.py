
from django.core.management.base import BaseCommand, CommandError

from dj_extras.mysql_utils import load_mysql_db


class Command(BaseCommand):
    args = ''
    help = 'Load Compressed mysql db into app'

    def handle(self, *args, **options):
        app_name_list= args
        for app_name in app_name_list:
            rval = load_mysql_db(app_name)

            if rval['error']:
                raise CommandError(rval['error'])