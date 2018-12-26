from __future__ import absolute_import

from django.test import TestCase
import pandas as pd
from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector


class PhoneDetectionTest(TestCase):
    def setUp(self):
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        self.data = pd.read_csv('ner_v2/tests/pattern/phone_number/data/phone_detection_test_cases.csv')
        self.test_dict = self.preprocess_test_cases()

    def preprocess_test_cases(self):
        self.data['original_entities'] = self.data['original_entities'].apply(lambda x: x.decode('utf-8'))

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

    def test_from_dict(self):
        for i in range(len(self.data)):
            message = self.test_dict['message'][i]
            expected_value = self.test_dict['expected_value'][i]
            detected_texts, original_texts = self.phone_number_detection.\
                detect_entity(text=message.decode('utf-8'))
            zipped = zip(detected_texts, original_texts)
            self.assertEqual(expected_value, zipped)
