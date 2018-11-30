from __future__ import absolute_import

from django.test import TestCase
import datetime
import pytz
import mock

from ner_v2.detectors.temporal.date.date_detection import DateAdvancedDetector


def mocked_get_weekdays_for_month(**kargs):
    return [1, 2]


class DateDetectionTest(TestCase):
    def setUp(self):
        self.entity_name = 'date'
        self.timezone = pytz.timezone('UTC')
        self.now_date = datetime.datetime.now(tz=self.timezone)

    def test_en_date_detection_date_range_ddth_of_mmm_to_ddth(self):
        """
        Date detection for pattern '2nd jan to 5th'
        """
        message = '2nd jan to 5th'
        day1 = 2
        day2 = 5
        month = 1
        year = self.now_date.year
        if self.now_date.month > 1:
            year += 1

        date_detector_object = DateAdvancedDetector(entity_name=self.entity_name, language='en')
        response = date_detector_object.detect_entity(message)

        self.assertJSONEqual(response[0][0], {'end_range': False, 'from': False, 'normal': False, 'start_range': True,
                                              'to': False, 'value':
                                                  {'dd': day1, 'mm': month, 'type': 'date', 'yy': year}})
        self.assertJSONEqual(response[0][1], {'end_range': False, 'from': False, 'normal': False, 'start_range': True,
                                              'to': False, 'value':
                                                  {'dd': day2, 'mm': month, 'type': 'date', 'yy': year}})
        self.assertEqual(response[1][0], message)
        self.assertEqual(response[1][1], message)

    @mock.patch('ner_v2.detectors.temporal.utils.get_weekdays_for_month', side_effect=mocked_get_weekdays_for_month)
    def test_en_date_detection_day_range_for_nth_week_month(self):
        """
        Date detection for pattern 'first week of jan'
        """
        message = 'first week of jan'
        month = 1
        year = self.now_date.year
        if self.now_date.month > month:
            year += 1

        date_detector_object = DateAdvancedDetector(entity_name=self.entity_name, language='en')
        response = date_detector_object.detect_entity(message)
        self.assertJSONEqual(response[0][0], {'end_range': False, 'from': False, 'normal': True, 'start_range': False,
                                              'to': False, 'value':
                                                  {'dd': 1, 'mm': month, 'type': 'date', 'yy': year}})
        self.assertJSONEqual(response[0][1], {'end_range': False, 'from': False, 'normal': True, 'start_range': False,
                                              'to': False, 'value':
                                                  {'dd': 2, 'mm': month, 'type': 'date', 'yy': year}})
        self.assertEqual(response[1][0], message)
        self.assertEqual(response[1][1], message)
