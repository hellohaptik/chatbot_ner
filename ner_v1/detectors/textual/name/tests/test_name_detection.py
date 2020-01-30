from __future__ import absolute_import

import os

import pandas as pd
from django.test import TestCase
import mock
import json

from ner_v1.constant import DATASTORE_VERIFIED, MODEL_VERIFIED
from ner_v1.detectors.textual.name.name_detection import NameDetector


class NameDetectionTest(TestCase):

    def setUp(self):
        self.csv_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_cases_person_name.csv')
        self.data = pd.read_csv(self.csv_file, encoding='utf-8')
        self.test_dict = self.preprocess_data()

    def preprocess_data(self):
        test_dict = {
            'language': [],
            'message': [],
            'expected_value': [],
            'mocked_values': [],
        }
        for (language, message, first_name, middle_name, last_name, original_entity, mocked_values) in zip(
                self.data['language'],
                self.data['message'],
                self.data['first_name'],
                self.data['middle_name'],
                self.data['last_name'],
                self.data['original_entities'],
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
            test_dict['message'].append(message)
            test_dict['expected_value'].append(temp)
            test_dict['mocked_values'].append(mocked_values)

        return test_dict

    @mock.patch.object(NameDetector, "text_detection_name")
    def test_person_name_detection(self, mock_text_detection_name):
        for i in range(len(self.data)):
            message = self.test_dict['message'][i]
            expected_value = self.test_dict['expected_value'][i]

            mock_text_detection_name.return_value = json.loads(self.test_dict['mocked_values'][i])

            name_detector = NameDetector(language=self.test_dict['language'][i], entity_name='person_name')
            detected_texts, original_texts = name_detector.detect_entity(text=message)
            for d in detected_texts:
                d.pop(MODEL_VERIFIED)
                d.pop(DATASTORE_VERIFIED)
            zipped = zip(detected_texts, original_texts)
            self.assertEqual(expected_value, zipped)

    def generate_person_name_dict(self, person_name_dict):
        for person_name_key in person_name_dict:
            if person_name_dict[person_name_key] == "None":
                person_name_dict[person_name_key] = None

        return person_name_dict
