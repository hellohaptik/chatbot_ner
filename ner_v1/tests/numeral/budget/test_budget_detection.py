from __future__ import absolute_import

from django.test import TestCase

from ner_v1.detectors.numeral.budget.budget_detection import BudgetDetector


class TestBudgetDetector(TestCase):
    def setUp(self):
        self.budget_detector = BudgetDetector(entity_name='budget')
        self.budget_detector.set_min_max_digits(min_digit=1, max_digit=15)

    @staticmethod
    def make_budget_dict(min_budget=0, max_budget=0):
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

    def test_not_budgets(self):
        """
        Test sentences that do not have any budget
        """
        tests = [
            'I want to buy 5liters of milk',
            'Your flight number is 9w998',
            'hello, your coupon code is Amazon50',
            'hello, your coupon code is 50Amazon',
            'the insect is 120millimeters tall'
        ]

        for test in tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertEqual(budget_dicts, [])
            self.assertEqual(original_texts, [])

    def test_budgets_without_scales(self):
        """
        Test budgets without scales
        """
        tests = [
            ('I want to buy 5 liters of milk', 0, 5, '5'),
            ('the insect is 120 millimeters tall', 0, 120, '120'),
            ('hello, your coupon code is 50 Amazon', 0, 50, '50'),
            ('Your flight number is 9w 998', 0, 998, '998'),
        ]
        for test, min_budget, max_budget, original_text in tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertEqual(budget_dicts, [self.make_budget_dict(max_budget=max_budget)])
            self.assertEqual(original_texts, [original_text])

    def test_all_budget_scales(self):
        """
        Test all supported budget scales
        """
        tests = [
            ('2k', 0, 2000, '2k'),
            ('2 thousand', 0, 2000, '2 thousand'),
            ('2 hazar', 0, 2000, '2 hazar'),
            ('2 hazaar', 0, 2000, '2 hazaar'),
            ('2 hajar', 0, 2000, '2 hajar'),
            ('2 hajaar', 0, 2000, '2 hajaar'),
            ('2l', 0, 200000, '2l'),
            ('2 lac', 0, 200000, '2 lac'),
            ('2 lacs', 0, 200000, '2 lacs'),
            ('2 lak', 0, 200000, '2 lak'),
            ('2 laks', 0, 200000, '2 laks'),
            ('2 lakh', 0, 200000, '2 lakh'),
            ('2 lakhs', 0, 200000, '2 lakhs'),
            ('2m', 0, 2000000, '2m'),
            ('2mn', 0, 2000000, '2mn'),
            ('2 mil', 0, 2000000, '2 mil'),
            ('2 mill', 0, 2000000, '2 mill'),
            ('2 million', 0, 2000000, '2 million'),
            ('2c', 0, 20000000, '2c'),
            ('2 cr', 0, 20000000, '2 cr'),
            ('2 cro', 0, 20000000, '2 cro'),
            ('2 cror', 0, 20000000, '2 cror'),
            ('2 crore', 0, 20000000, '2 crore'),
            ('2 crores', 0, 20000000, '2 crores'),
        ]

        for test, min_budget, max_budget, original_text in tests:
            budget_dicts, original_texts = self.budget_detector.detect_entity(text=test)
            self.assertEqual(budget_dicts, [self.make_budget_dict(max_budget=max_budget)])
            self.assertEqual(original_texts, [original_text])
