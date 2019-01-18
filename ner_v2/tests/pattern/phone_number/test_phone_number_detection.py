from __future__ import absolute_import

import os
import pandas as pd
from django.test import TestCase

from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector


class PhoneDetectionTest(TestCase):
    def setUp(self):
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        self.csv_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                     'data',
                                     'phone_detection_test_cases.csv')
        self.data = pd.read_csv(self.csv_path, encoding='utf-8')
        self.test_dict = self.preprocess_test_cases()

    def preprocess_test_cases(self):
        test_dict = {
            'language': [],
            'message': [],
            'expected_value': [],
        }
        for language, message, detected_entity, original_entity in zip(self.data['language'], self.data['message'],
                                                                       self.data['detected_entities'],
                                                                       self.data['original_entities']):
            de, oe = [], []
            de.extend(detected_entity.split('|'))
            oe.extend(original_entity.split('|'))
            temp = []
            for d, o in zip(de, oe):
                temp.append((d, o))
            test_dict['language'].append(language)
            test_dict['message'].append(message)
            test_dict['expected_value'].append(temp)

        return test_dict

    def test_phone_number_detection(self):
        for i in range(len(self.data)):
            message = self.test_dict['message'][i]
            expected_value = self.test_dict['expected_value'][i]
            detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
            zipped = zip(detected_texts, original_texts)
            self.assertEqual(expected_value, zipped)
