from __future__ import absolute_import

import os

import pandas as pd
import six
from django.test import TestCase

from ner_v2.detectors.temporal.time.time_detection import TimeDetector


class TimeDetectorTest(TestCase):
    LANGUAGE = 'language'
    TEXT = 'text'
    BOT_MESAGE = 'bot_message'
    HH = 'hh'
    MM = 'mm'
    NN = 'nn'
    RANGE = 'range'
    TIME_TYPE = 'time_type'
    ORIGINAL_TEXT = 'original_text'
    NA_VALUES = ('NA', 'na', None,)
    MULTI_SEPARATOR = '|'

    def setUp(self):
        self.csv_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'time_detection_tests.csv')

    def is_nan(self, value):
        # type: (Any) -> bool
        return value in TimeDetectorTest.NA_VALUES

    def _make_expected_output(self, row_dict, drop_na=True):
        # type: (dict, bool) -> Tuple[List[Dict[str, Any]], List[Union[str, unicode]]]
        # TODO: This function should be a part of time detection package
        if self.is_nan(row_dict[TimeDetectorTest.ORIGINAL_TEXT]):
            return [], []

        hhs = [int(part) for part in row_dict[TimeDetectorTest.HH].split(TimeDetectorTest.MULTI_SEPARATOR)]
        mms = [int(part) for part in row_dict[TimeDetectorTest.MM].split(TimeDetectorTest.MULTI_SEPARATOR)]
        nns = row_dict[TimeDetectorTest.NN].split(TimeDetectorTest.MULTI_SEPARATOR)
        ranges = row_dict[TimeDetectorTest.RANGE].split(TimeDetectorTest.MULTI_SEPARATOR)
        time_types = row_dict[TimeDetectorTest.TIME_TYPE].split(TimeDetectorTest.MULTI_SEPARATOR)
        original_texts = [part.lower()
                          for part in row_dict[TimeDetectorTest.ORIGINAL_TEXT].split(TimeDetectorTest.MULTI_SEPARATOR)]

        if not all(other_list_size == len(original_texts)
                   for other_list_size in [len(hhs), len(mms), len(nns), len(ranges), len(time_types)]):
            raise ValueError('Ill formatted test case row, all output rows must have same number of parts separated by'
                             '{}'.format(TimeDetectorTest.MULTI_SEPARATOR))

        expected_times = []
        for (hh, mm, nn, range_, time_type) in zip(hhs, mms, nns, ranges, time_types):
            output = {
                'hh': hh,
                'mm': mm,
                'nn': nn,
                'range': range_,
                'time_type': time_type,
            }
            if drop_na:
                output = {k: output[k] for k in output if not self.is_nan(output[k])}
            expected_times.append(output)
        return expected_times, original_texts

    def test_time_detection_from_csv(self):
        """
        Run time detection tests defined in the csv
        """
        # columns = ['language', 'text', 'bot_message', 'hh', 'mm', 'nn', 'range', 'time_type', 'original_text']
        df = pd.read_csv(self.csv_path, encoding='utf-8', dtype=six.text_type, keep_default_na=False)

        for language, language_tests_df in df.groupby(by=[TimeDetectorTest.LANGUAGE]):
            print('Running tests for language {}'.format(language))
            time_detector = TimeDetector(language=language)
            for index, row in language_tests_df.iterrows():
                if not self.is_nan(row[TimeDetectorTest.BOT_MESAGE]):
                    time_detector.set_bot_message(bot_message=row[TimeDetectorTest.BOT_MESAGE])
                range_enabled = not self.is_nan(row[TimeDetectorTest.RANGE])
                expected_times, expected_original_texts = self._make_expected_output(row_dict=row)
                expected_output = list(zip(expected_times, expected_original_texts))
                detected_times, original_texts = time_detector.detect_entity(text=row[TimeDetectorTest.TEXT],
                                                                                 range_enabled=range_enabled)

                for detected_output_pair in zip(detected_times, original_texts):
                    self.assertIn(detected_output_pair, expected_output)
