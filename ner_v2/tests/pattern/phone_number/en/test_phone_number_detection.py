from __future__ import absolute_import

from django.test import TestCase

from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector


class PhoneDetectionTest(TestCase):
    def setUp(self):
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')

    def test_phone_detection_landline_no_spaces(self):
        message = 'Call the number 26129854'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('26129854', u'26129854')]), zipped)

    def test_phone_detection_landline_with_no_spaces_area_code(self):
        message = 'Set a reminder on 02226129854'
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('02226129854', u'02226129854')]), zipped)

    def test_phone_detection_landline_with_spaces_area_code(self):
        message = 'Set a reminder on 022 26129854'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('02226129854', u'022 26129854')]), zipped)

    def test_phone_detection_mobile_no_spaces(self):
        message = 'Call the number 9820334455'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('9820334455', u'9820334455')]), zipped)

    def test_phone_detection_mobile_with_no_spaces_code(self):
        message = 'Set a reminder on 919820334455'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('919820334455', u'919820334455')]), zipped)

    def test_phone_detection_mobile_with_spaces_code(self):
        message = 'Set a reminder on 91 9820334455'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('919820334455', u'91 9820334455')]), zipped)

    def test_phone_detection_mobile_with_spaces_code_plus(self):
        message = 'Set a reminder on +91 9820334455'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('919820334455', u'+91 9820334455')]), zipped)

    def test_phone_detection_mobile_no_spaces_code_plus(self):
        message = 'Set a reminder on +919820334455'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('919820334455', u'+919820334455')]), zipped)

    def test_phone_detection_mobile_with_spaces_code_hyphens(self):
        message = 'Set a reminder on 91 9820-3344-55'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('919820334455', u'91 9820-3344-55')]), zipped)

    def test_phone_detection_mobile_international_brackets_hyphens(self):
        message = 'Set a reminder on +1 (408) 912-6172'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('14089126172', u'+1 (408) 912-6172')]), zipped)

    def test_phone_detection_mobile_international_plus(self):
        message = 'Set a reminder on +1 408 9126172'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('14089126172', u'+1 408 9126172')]), zipped)

    def test_phone_detection_mobile_international(self):
        message = 'Set a reminder on 14089126172'
        self.phone_number_detection = PhoneDetector(entity_name='phone_number')
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('14089126172', u'14089126172')]), zipped)

    def test_phone_detection_two_phone_nunbers(self):
        message = 'Send 1000rs to 14089126172 and call 26129854'
        detected_texts, original_texts = self.phone_number_detection.detect_entity(text=message)
        zipped = zip(detected_texts, original_texts)
        self.assertEqual(([('14089126172', u'14089126172'), ('26129854', u'26129854')]), zipped)
