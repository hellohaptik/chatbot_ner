from __future__ import absolute_import
import os

from django.test import TestCase
import datetime
import pytz
import pandas as pd
#import mock

from ner_v2.detectors.temporal.date.date_detection import DateDetector

class DateDetectionTest(TestCase):
    def setUp(self):
        self.entity_name = 'date'
        self.timezone = pytz.timezone('UTC')
        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    @staticmethod
    def test_basic_patterns(self):
        list_languages = os.listdir(self.TEST_DATA_DIR)
        for lang in list_languages:
            file_basic_patterns = os.path.join(self.TEST_DATA_DIR, lang, 'basic_test_case.csv')
            if os.path.isfile(file_basic_patterns):
                self.data = pd.read_csv(file_basic_patterns)
                date_detector = DateDetector(self.entity_name, language=lang)
