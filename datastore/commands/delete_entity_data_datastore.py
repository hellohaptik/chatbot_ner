from __future__ import absolute_import
from django.core.management.base import BaseCommand
from datastore import DataStore


class Command(BaseCommand):
    help = 'Delete entity data from DataStore'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entity_name',
            default=False,
            help='name of the entity to delete',
        )

    def handle(self, *args, **options):
        if 'entity_name' in options and options['entity_name']:
            entity_name = options['entity_name']
            db = DataStore()
            db.delete_entity(entity_name=entity_name)
            self.stdout.write('Successfully deleted entity data for "%s"' % entity_name)
        else:
            self.stdout.write(self.style.ERROR('argument --entity_name required'))
