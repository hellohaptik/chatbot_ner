import pandas as pd
from __future__ import absolute_import
from django.test import TestCase

from ner_v1.detectors.textual.name.name_detection import NameDetector

class NameDetectionTest(TestCase):

    def setUp(self):
        self.data = pd.read_csv()

    def preprocess_data(self):
        data = pd.read_csv('')
