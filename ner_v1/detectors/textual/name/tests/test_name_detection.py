from __future__ import absolute_import
import pandas as pd
from django.test import TestCase
from ner_v1.detectors.textual.name.name_detection import NameDetector


class NameDetectionTest(TestCase):

    def setUp(self):
        self.data = pd.read_csv('ner_v1/detectors/textual/name/tests/test_cases_person_name.csv')
        self.test_dict = self.preprocess_data()

    def runTest(self):
        self.data = pd.read_csv('ner_v1/detectors/textual/name/tests/test_cases_person_name.csv')
        self.test_dict = self.preprocess_data()
        self.test_person_name_detection()

    def preprocess_data(self):
        self.data = pd.read_csv('name_test.csv')
        self.data['original_entities'] = self.data['original_entities'].apply(lambda x: x.decode('utf-8'))

        test_dict = {
            'language': [],
            'message': [],
            'expected_value': [],
        }
        for language, message, first_name, middle_name, last_name, original_entity in zip(self.data['language'],
                                                                       self.data['message'],
                                                                       self.data['first_name'],
                                                                       self.data['middle_name'],
                                                                       self.data['last_name'],
                                                                       self.data['original_entities']):
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

        return test_dict

    def test_person_name_detection(self):
        for i in range(len(self.data)):
            message = self.test_dict['message'][i]
            print(message)
            expected_value = self.test_dict['expected_value'][i]
            name_detector = NameDetector(language_script=self.test_dict['language'][i],
                                         entity_name='person_name')
            detected_texts, original_texts = name_detector.\
                detect_entity(text=message.decode('utf-8'))
            zipped = zip(detected_texts, original_texts)
            print(detected_texts, original_texts)
            self.assertEqual(expected_value, zipped)

    def generate_person_name_dict(self, person_name_dict):
        for person_name_key in person_name_dict:
            if person_name_dict[person_name_key] == "None":
                person_name_dict[person_name_key] = None
            else:
                person_name_dict[person_name_key] = person_name_dict[person_name_key].decode('utf-8')

        return person_name_dict
