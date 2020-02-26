from __future__ import absolute_import
import os
from django.core.management.base import BaseCommand
from datastore import DataStore


class Command(BaseCommand):
    help = 'Populate DataStore with entity data read from csv files stored at entity_data_directory_path argument ' \
           'and csv files at paths specified by csv_file_paths argument'

    def add_arguments(self, parser):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        data_dir = os.path.join(base_dir, 'data', 'entity_data')
        parser.add_argument(
            '--entity_data_directory_path',
            default=data_dir,
            help='complete path to directory containing csv files. Default value is %s' % data_dir,
        )

        parser.add_argument(
            '--csv_file_paths',
            default=None,
            help='comma separated file paths to individual csv files',
        )

    def handle(self, *args, **options):
        entity_data_directory_path = None
        csv_file_paths = None
        if ('entity_data_directory_path' in options and options['entity_data_directory_path']) or \
                ('csv_file_paths' in options and options['csv_file_paths']):

            if 'entity_data_directory_path' in options and options['entity_data_directory_path']:
                entity_data_directory_path = options['entity_data_directory_path']
                if not os.path.exists(entity_data_directory_path):
                    entity_data_directory_path = None

            if 'csv_file_paths' in options and options['csv_file_paths']:
                csv_file_paths = options['csv_file_paths'].split(',')
                csv_file_paths = [csv_file_path for csv_file_path in csv_file_paths if csv_file_path and
                                  csv_file_path.endswith('.csv')]
            db = DataStore()
            db.populate(entity_data_directory_path=entity_data_directory_path, csv_file_paths=csv_file_paths)
            if entity_data_directory_path:
                self.stdout.write(
                    'Successfully populated entity data from csv files at "%s"' % entity_data_directory_path)
            if csv_file_paths:
                self.stdout.write('Successfully populated entity data from %d other csv file(s)"'
                                  % len(csv_file_paths))
        else:
            self.stdout.write(self.style.ERROR('argument --entity_data_directory_path or --csv_file_paths required'))
