
from django.core.management.base import BaseCommand, CommandError

from mysql_utils import dump_mysql_db

class Command(BaseCommand):
    args = ''
    help = 'Dump App Databases via mysqldump'

    def handle(self, *args, **options):

        app_name_list= args
        for app_name in app_name_list:
            rval = dump_mysql_db(app_name)

            if rval['error']:
                raise CommandError(rval['error'])
#
## THis script is for dumping big static tables so we can create them elsewhere with little effort
##
#echo "Dumping gene data"
#mysqldump -udjango -pdjango  --no-create-info --opt  dj_henez genedb_exon genedb_exonmerge genedb_exonmerge_exons genedb_genemerge genedb_genemerge_gene_transcripts genedb_genetranscript  | gzip  > ~/Data/mysql/gene_db.sql.gz
#
#echo "Dumping Variant Data"
#mysqldump -udjango -pdjango --no-create-info --opt dj_henez variant_variantgenemodel v