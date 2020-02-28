from __future__ import absolute_import
from django.core.management.base import BaseCommand
from datastore import DataStore


class Command(BaseCommand):
    help = 'Deletes the DataStore strcuture and all the data in it.'

    def handle(self, *args, **options):
        db = DataStore()
        if db.exists():
            db.delete()
            self.stdout.write('Successfully deleted DataStore structure and data.')
        else:
            self.stdout.write('DataStore structure not created. Skipping delete action')
