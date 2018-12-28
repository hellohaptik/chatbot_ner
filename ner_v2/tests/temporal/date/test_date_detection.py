from __future__ import absolute_import

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

    # @staticmethod
    # def test_basic_patterns(self):
    #     self.data = pd.read_csv('ner_v2/tests/temporal/date/data/basic_test_case.csv')
    #     self.data['original_text'] = self.data['original_text'].apply(lambda x: x.decode('utf-8'))
    #     for