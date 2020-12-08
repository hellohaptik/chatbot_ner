from __future__ import absolute_import

import os

import pandas as pd
from django.test import TestCase

from ner_v1.constant import DATASTORE_VERIFIED, MODEL_VERIFIED
from ner_v1.detectors.textual.name.name_detection import NameDetector
from six.moves import range
from six.moves import zip


class NameDetectionTest(TestCase):

    def setUp(self):
        self.csv_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_cases_person_name.csv')
        self.data = pd.read_csv(self.csv_file, encoding='utf-8')
        self.test_dict = self.preprocess_data()

    def preprocess_data(self):
        test_dict = {
            'language': [],
            'message': [],
            'bot_message': [],
            'expected_value': [],
            'mocked_values': [],
        }
        for (
                language, bot_message, message, first_name, middle_name, last_name, original_entity, mocked_values
        ) in zip(self.data['language'], self.data['bot_message'], self.data['message'], self.data['first_name'],
                 self.data['middle_name'], self.data['last_name'], self.data['original_entities'],
                 self.data['mocked_values']):

            fn = []
            mn = []
            ln = []
            oe = []

            fn.extend(first_name.split('|'))
            mn.extend(middle_name.split('|'))
            ln.extend(last_name.split('|'))
            oe.extend(original_entity.split('|'))

            temp = []
            for f, m, l, o in zip(fn, mn, ln, oe):
                temp.append((self.generate_person_name_dict(person_name_dict={
                    'first_name': f,
                    'middle_name': m,
                    'last_name': l
                }), o))
            test_dict['language'].append(language)
            test_dict['bot_message'].append(bot_message)
            test_dict['message'].append(message)
            test_dict['expected_value'].append(temp)
            test_dict['mocked_values'].append(mocked_values)

        return test_dict

    def test_person_name_detection(self):
        for i in range(len(self.data)):
            message = self.test_dict['message'][i]
            bot_message = self.test_dict['bot_message'][i]
            expected_value = self.test_dict['expected_value'][i]
            name_detector = NameDetector(language=self.test_dict['language'][i], entity_name='person_name')
            detected_texts, original_texts = name_detector.detect_entity(text=message,
                                                                         bot_message=bot_message)
            for d in detected_texts:
                d.pop(MODEL_VERIFIED)
                d.pop(DATASTORE_VERIFIED)
            zipped = list(zip(detected_texts, original_texts))
            self.assertEqual(expected_value, zipped)

    def generate_person_name_dict(self, person_name_dict):
        for person_name_key in person_name_dict:
            if person_name_dict[person_name_key] == "None":
                person_name_dict[person_name_key] = None

        return person_name_dict
