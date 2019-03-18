from __future__ import absolute_import

from django.test import TestCase

from ner_v1.detectors.numeral.budget.budget_detection import BudgetDetector


class TestBudgetDetector(TestCase):
    def setUp(self):
        self.budget_detector = BudgetDetector(entity_name='budget')
        self.budget_detector.set_min_max_digits(min_digit=1, max_digit=15)

    def make_budget_dict(self, min_budget=0, max_budget=0):
        return {'min_budget': min_budget, 'max_budget': max_budget, 'type': 'normal_budget'}

    def test_min_max_digits_limits(self):
        """
        Test min max digits limit
        """
        self.budget_detector.set_min_max_digits(min_digit=2, max_digit=5)

        positive_tests = [
            'Show products in 10,000 - 20,000 range',
            'This costs about 10 rs',
        ]

        negative_tests = [
            'my budget is .5cr',
            'Annual operating budget is 1.2cr',
            'Show me cars that cost less than 2.99mil',
            'Rs. 1 is the minimum denomination'
        ]

        for test in positive_tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertTrue(original_texts)

        for test in negative_tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertFalse(original_texts)

    def test_max_budget(self):
        """
        Test v1 max budget
        """
        tests = [
            ('Show me cars that cost below rs. 5000', 0, 5000, 'below rs. 5000'),
            ('Show me cars that cost less than 6k', 0, 6000, 'less than 6k'),
            ('at most 30 rs.', 0, 30, 'at most 30 rs.'),
            ('costs upto Rs.100', 0, 100, 'upto rs.100')
        ]
        for test, min_budget, max_budget, original_text in tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertEqual(budget_dicts, [self.make_budget_dict(max_budget=max_budget)])
            self.assertEqual(original_texts, [original_text])

    def test_min_budget(self):
        """
        Test v1 min budget
        """
        tests = [
            ('Show me cars that cost above rs. 5000', 5000, 0, 'above rs. 5000'),
            ('Show me cars that cost more than 6k', 6000, 0, 'more than 6k'),
            ('at least 30 rs.', 30, 0, 'at least 30 rs.'),
            ('costs greater than Rs.100', 100, 0, 'greater than rs.100'),
        ]
        for test, min_budget, max_budget, original_text in tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertEqual(budget_dicts, [self.make_budget_dict(min_budget=min_budget)])
            self.assertEqual(original_texts, [original_text])

    def test_range(self):
        """
        Test v1 budget range
        """
        tests = [
            ('Show products in 10,000 - 20,000 range', 10000, 20000, '10,000 - 20,000'),
            ('Show products in 10,000-20,000 range', 10000, 20000, '10,000-20,000'),
            ('Show products in 10,000 till Rs. 20k range', 10000, 20000, '10,000 till rs. 20k'),
            ('Show products from rs. 5,5,00 to 6,0,0,0 rupees', 5500, 6000, 'rs. 5,5,00 to 6,0,0,0 rupees'),
        ]
        for test, min_budget, max_budget, original_text in tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertEqual(budget_dicts, [self.make_budget_dict(min_budget=min_budget, max_budget=max_budget)])
            self.assertEqual(original_texts, [original_text])

    def test_any_budget(self):
        """
        Test v1 budget any
        """
        tests = [
            ('.5cr', 0, 5000000, '.5cr'),
            ('1.2cr', 0, 12000000, '1.2cr'),
            ('1.5 thousand', 0, 1500, '1.5 thousand'),
            ('5 hazar', 0, 5000, '5 hazar'),
            ('10 rs', 0, 10, '10 rs'),
        ]
        for test, min_budget, max_budget, original_text in tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertEqual(budget_dicts, [self.make_budget_dict(max_budget=max_budget)])
            self.assertEqual(original_texts, [original_text])
