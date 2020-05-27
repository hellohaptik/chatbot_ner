from __future__ import absolute_import

import re

from django.test import TestCase

from ner_v1.detectors.pattern.regex.regex_detection import RegexDetector


class TestRegexDetector(TestCase):
    def test_max_matches(self):
        """Test max_matches argument for RegexDetector"""
        entity_name = 'num'
        tag = '__{}__'.format(entity_name)
        pattern = '\\b(\\d+|)\\b'
        text = 'there are some numbers like 345 and 2342, but the pattern is bad too it matches empty string! We ' \
               'will now sprinkle this text with numbers 34634653 42342345234 12433345325 to test 17293847 345 2342'

        regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern, max_matches=3)
        expected_values = ['345', '2342', '34634653']
        expected_original_texts = ['345', '2342', '34634653']
        expected_tagged_text = 'there are some numbers like {t} and {t}, but the pattern is bad too ' \
                               'it matches empty string! We will now sprinkle this text with' \
                               ' numbers {t} 42342345234 12433345325 to test 17293847 345 2342'.format(t=tag)
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

        regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern, max_matches=50)
        expected_values = ['345', '2342', '34634653', '42342345234', '12433345325', '17293847', '345', '2342']
        expected_original_texts = ['345', '2342', '34634653', '42342345234', '12433345325', '17293847', '345', '2342']
        expected_tagged_text = 'there are some numbers like {t} and {t}, but the pattern is bad too ' \
                               'it matches empty string! We will now sprinkle this text with' \
                               ' numbers {t} {t} {t} to test {t} {t} {t}'.format(t=tag)
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

    def test_non_empty_matches(self):
        """Test if RegexDetector returns only non empty matches"""
        entity_name = 'test'
        _ = '__{}__'.format(entity_name)
        pattern = '\\b(\\d+|)\\b'
        text = 'there are no numbers in this text! but the pattern is bad too, it matches empty string'

        regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern)
        expected_values = []
        expected_original_texts = []
        expected_tagged_text = text
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

    def test_recursive_replace(self):
        """Test protection against MemoryError when replacing in RegexDetector"""
        multiplier = 30
        entity_name = 'abab'
        tag = '__{}__'.format(entity_name)
        pattern = '\\bab\\b'
        text = ' '.join(['ab'] * multiplier)

        regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern)
        expected_values = ['ab'] * multiplier
        expected_original_texts = ['ab'] * multiplier
        expected_tagged_text = ' '.join(['{t}'.format(t=tag)] * multiplier)
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

    def test_dot_star(self):
        """Test .* pattern for RegexDetector"""
        entity_name = 'test'
        tag = '__{}__'.format(entity_name)
        pattern = '.*'
        text = 'hello world\nlorem ipsum dolor sit amet\ntest with new lines and stuff .^!@"#$%^&*(){}[]:?><\n'

        regex_detector = RegexDetector(entity_name=entity_name, pattern=pattern)
        expected_values = ['hello world', 'lorem ipsum dolor sit amet',
                           'test with new lines and stuff .^!@"#$%^&*(){}[]:?><']
        expected_original_texts = ['hello world', 'lorem ipsum dolor sit amet',
                                   'test with new lines and stuff .^!@"#$%^&*(){}[]:?><']
        expected_tagged_text = '{t}\n{t}\n{t}\n'.format(t=tag)
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)

        regex_detector = RegexDetector(entity_name=entity_name, re_flags=RegexDetector.DEFAULT_FLAGS | re.DOTALL,
                                       pattern=pattern)
        expected_values = [text]
        expected_original_texts = [text]
        expected_tagged_text = '{t}'.format(t=tag)
        values, original_texts = regex_detector.detect_entity(text)
        self.assertEqual(regex_detector.tagged_text, expected_tagged_text)
        self.assertEqual(values, expected_values)
        self.assertEqual(original_texts, expected_original_texts)
