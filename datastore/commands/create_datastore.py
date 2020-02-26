from __future__ import absolute_import
from django.core.management.base import BaseCommand
from datastore import DataStore


class Command(BaseCommand):
    help = 'Creates the DataStore skeleton.'

    def handle(self, *args, **options):
        db = DataStore()
        if db.exists():
            self.stdout.write('DataStore structure already created, skipping this action. '
                              'If you want to recreate it, run python manage.py delete_datastore first.')
        else:
            db.create()
            self.stdout.write('Successfully created DataStore structure')
