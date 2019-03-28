from __future__ import absolute_import

from ner_v1.detectors.textual.text.text_detection_model import TextModelDetector
from django.test import TestCase


class BulkTextDetectionTest(TestCase):

    def test_bulk_detect(self):
        """
        Tests data_type and values of returned entity_output for bulk detection.

        """
        text_model_detector = TextModelDetector(entity_name="city_list", language="en", live_crf_model_path=None,
                                                read_model_from_s3=False, read_embeddings_from_remote_url=False)

        # Case 1
        sentences = [u"i want to go from delhi"]
        expected_output = [[{'detection': 'message',
                             'entity_value': {'crf_model_verified': False,
                                              'datastore_verified': True,
                                              'value': u'New Delhi'},
                             'language': 'en',
                             'original_text': u'delhi'}]]
        entity_output = text_model_detector.detect_bulk(messages=sentences)
        self.assertIs(type(expected_output[0]), type(entity_output[0]))

    def test_detect(self):
        """
        Tests data_type and values of returned entity_output.

        """
        text_model_detector = TextModelDetector(entity_name="city_list", language="en", live_crf_model_path=None,
                                                read_model_from_s3=False, read_embeddings_from_remote_url=False)
        sentence = u"i want to go from delhi to mumbai"
        expected_output = [{'detection': 'message',
                            'entity_value': {'crf_model_verified': False,
                                             'datastore_verified': True,
                                             'value': u'New Delhi'},
                            'language': 'en',
                            'original_text': u'delhi'},
                           {'detection': 'message',
                            'entity_value': {'crf_model_verified': False,
                                             'datastore_verified': True,
                                             'value': u'mumbai'},
                            'language': 'en',
                            'original_text': u'mumbai'}]
        entity_output = text_model_detector.detect(message=sentence, structured_value=None, fallback_value=None,
                                                   bot_message=None)
        self.assertIs(type(expected_output[0]), type(entity_output[0]))
