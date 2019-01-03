from __future__ import absolute_import
import os

import six
from django.test import TestCase
import datetime
import pytz
import pandas as pd
# import mock

from ner_v2.detectors.temporal.date.date_detection import DateDetector
import ner_v2.detectors.temporal.constant as const


class DateDetectionTest(TestCase):
    def setUp(self):
        self.entity_name = 'date'
        self.timezone = pytz.timezone('UTC')
        self.now_date = datetime.datetime.now(tz=self.timezone)
        self.TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    @staticmethod
    def _make_expected_output(dd, mm, yy, date_type=const.TYPE_EXACT):
        # TBD: This function should be a part of date detection class
        output = {
            'dd': dd,
            'mm': mm,
            'yy': yy,
            'type': date_type
        }
        return output

    def test_basic_patterns(self):
        """
        This function tests basic patterns of date such as dd-mm-yy, dd/mm/yyyy, dd month, yyyy etc. It is limited to
        testing only single occurrence in a message and validates 'detect_entity' function of date detector.
        
        For example - My birthday is 18th January, 1992
        
        #TBD End to end output dictionary not validated in this function.
        """
        # columns = ['message', 'dd', 'mm', 'yy', 'original_text']
        dtype = {
            'message': six.text_type,
            'dd': int,
            'mm': int,
            'yy': int,
            'original_text': six.text_type
        }
        list_languages = os.listdir(self.TEST_DATA_DIR)
        for lang in list_languages:
            file_basic_patterns = os.path.join(self.TEST_DATA_DIR, lang, 'basic_test_case.csv')
            if os.path.isfile(file_basic_patterns):
                df_test_data = pd.read_csv(file_basic_patterns, encoding='utf-8', dtype=dtype)
                date_detector = DateDetector(self.entity_name, language=lang)
                for index, row in df_test_data.iterrows():
                    expected_output = self._make_expected_output(row['dd'], row['mm'], row['yy'])
                    expected_original_text = row['original_text']
                    detected_date_list, detected_original_text = date_detector.detect_entity(row['message'])
                    self.assertEqual(len(detected_date_list), 1)
                    self.assertEqual(expected_output, detected_date_list[0])
                    self.assertEqual(expected_original_text, detected_original_text[0])
