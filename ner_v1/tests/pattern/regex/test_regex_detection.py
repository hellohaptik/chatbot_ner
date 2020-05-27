from __future__ import absolute_import

from django.test import TestCase

from ner_v1.detectors.pattern.regex.regex_detection import RegexDetector


class TestRegexDetector(TestCase):
    def test_max_matches(self):
        entity_name = 'num'
        pattern = '\\b(\d+|)\\b'
        text = 'there are some numbers like 345 and 2342, but the pattern is bad too it matches empty string! We ' \
               'will now sprinkle this text with numbers 34634653 42342345234 12433345325 to test 17293847 345 2342'

        regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern, max_matches=3)
        expected_values = ['345', '2342', '34634653']
        expected_original_texts = ['345', '2342', '34634653']
        expected_tagged_text = 'there are some numbers like __num__ and __num__, but the pattern is bad too ' \
                               'it matches empty string! We will now sprinkle this text with' \
                               ' numbers __num__ 42342345234 12433345325 to test 17293847 345 2342'
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

        regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern, max_matches=50)
        expected_values = ['345', '2342', '34634653', '42342345234', '12433345325', '17293847', '345', '2342']
        expected_original_texts = ['345', '2342', '34634653', '42342345234', '12433345325', '17293847', '345', '2342']
        expected_tagged_text = 'there are some numbers like __num__ and __num__, but the pattern is bad too ' \
                               'it matches empty string! We will now sprinkle this text with' \
                               ' numbers __num__ __num__ __num__ to test __num__ __num__ __num__'
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

    def test_non_empty_matches(self):
        regex_detector = RegexDetector(entity_name='test', pattern='\\b(\d|)\\b')
        text = 'there are no numbers in this text! but the pattern is bad too, it matches empty string'
        expected_values = []
        expected_original_texts = []
        expected_tagged_text = text
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

    def test_recursive_replace(self):
        """Test protection against MemoryError when replacing"""
        multiplier = 30
        regex_detector = RegexDetector(entity_name='abab', pattern='\\bab\\b')
        text = ' '.join(['ab'] * multiplier)
        expected_values = ['ab'] * multiplier
        expected_original_texts = ['ab'] * multiplier
        expected_tagged_text = ' '.join(['__abab__'] * multiplier)
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)
