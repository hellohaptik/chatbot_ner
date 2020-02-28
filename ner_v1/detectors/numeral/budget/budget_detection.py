from __future__ import absolute_import
import re
from language_utilities.constant import ENGLISH_LANG
from ner_v1.constant import BUDGET_TYPE_NORMAL, BUDGET_TYPE_TEXT
from ner_v1.detectors.base_detector import BaseDetector
from ner_v1.detectors.textual.text.text_detection import TextDetector
from six.moves import zip


class BudgetDetector(BaseDetector):
    """Detects budget from the text  and tags them.

    Detects the budget from the text and replaces them by entity_name.
    This detection logic first checks for budget using regular expressions and also uses TextDetector class to extract
    data in textual format (i.e. Hundred, Thousand, etc).

    This detector captures  additional attributes like max_budget, min_budget whether the budget is
    normal_budget (detected through regex) or text_budget (detected through text detection)

    For Example:

        budget_detection = BudgetDetector('budget')
        message = "shirts between 2000 to 3000"
        budget_list, original_text = budget_detection.detect_entity(message)
        tagged_text = budget_detection.tagged_text
        print budget_list, ' -- ', original_text
        print 'Tagged text: ', tagged_text

         >> [{'max_budget': 3000, 'type': 'normal_budget', 'min_budget': 2000}]  --  ['2000 to 3000']
            Tagged text:  shirts between __budget__

        budget_detection = BudgetDetector('budget')
        message = "tshirts less than 2k"
        budget_list, original_text = budget_detection.detect_entity(message)
        tagged_text = budget_detection.tagged_text
        print budget_list, ' -- ', original_text
        print 'Tagged text: ', tagged_text

         >> [{'max_budget': 2000, 'type': 'normal_budget', 'min_budget': 0}]  --  ['less than 2k']
            Tagged text:  tshirts __budget__

        budget_detection = BudgetDetector('budget')
        message = "tshirts greater than 2k"
        budget_list, original_text = budget_detection.detect_entity(message)
        tagged_text = budget_detection.tagged_text
        print budget_list, ' -- ', original_text
        print 'Tagged text: ', tagged_text

         >> [{'max_budget': 0, 'type': 'normal_budget', 'min_budget': 2000}]  --  ['greater than 2k']
            Tagged text:  tshirts __budget__

        budget_detection = BudgetDetector('budget')
        message = "jeans of Rs. 1000"
        budget_list, original_text = budget_detection.detect_entity(message)
        tagged_text = budget_detection.tagged_text
        print budget_list, ' -- ', original_text
        print 'Tagged text: ', tagged_text

         >> [{'max_budget': 1000, 'type': 'normal_budget', 'min_budget': 0}]  --  ['rs. 1000']
            Tagged text:  ' jeans of __budget__ '


    Attributes:
        min_digit: minimum digit that a budget can take by default it is set to 2. So, the NER will detect number as
        budget if its greater then 9
        max_digit: maximum digit that buget can take by default it is set to 5. So, the NER will detect number
        as budget if its less than 99999
        text: string to extract entities from
        entity_name: string by which the detected size would be replaced with on calling detect_entity()
        tagged_text: string with size replaced with tag defined by entity name
        processed_text: string with sizes detected removed
        budget: list of budgets detected
        original_budget_text: list to store substrings of the text detected as budget
        tag: entity_name prepended and appended with '__'
        
    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)

    """

    _scale_patterns = {
        'k': 1000,
        'ha?zaa?r': 1000,
        'ha?ja?ar': 1000,
        'thousa?nd': 1000,
        'l': 100000,
        'lacs?': 100000,
        'lakh?s?': 100000,
        'lakhs': 100000,
        'm': 1000000,
        'mn': 1000000,
        'million': 1000000,
        'mill?': 1000000,
        'c': 10000000,
        'cro?': 10000000,
        'crore?s?': 10000000,
    }

    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False,
                 use_text_detection=False):
        """Initializes a BudgetDetector object

        Args:
            entity_name: A string by which the detected budget would be replaced with on calling detect_entity()
        """

        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(BudgetDetector, self).__init__(source_language_script, translation_enabled)

        self.min_digit = 2
        self.max_digit = 5
        self.entity_name = entity_name

        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.budget = []
        self.original_budget_text = []
        self.tag = '__' + self.entity_name + '__'
        self._use_text_detection = use_text_detection

        units, scales = list(zip(*sorted(
            list(BudgetDetector._scale_patterns.items()), key=lambda pattern_scale: len(pattern_scale[0]), reverse=True
        )))
        self._scale_compiled_patterns = [(scale, re.compile(unit)) for scale, unit in zip(scales, units)]
        digits_pattern = r'((?:\d+(?:\,\d+)*(?:\.\d+)?)|(?:(?:\d+(?:\,\d+)*)?(?:\.\d+)))'
        units_pattern = r'({})?'.format('|'.join(units))
        self._budget_pattern = r'(?:rs\.|rs|rupees|rupee)?' \
                               r'\s*{}\s*{}\s*' \
                               r'(?:rs\.|rs|rupees|rupee)?'.format(digits_pattern, units_pattern)

    def get_scale(self, unit):
        if unit:
            for scale, pattern in self._scale_compiled_patterns:
                if pattern.search(unit):
                    return scale

        return 1

    def detect_entity(self, text, **kwargs):
        """Detects budget in the text string

        Args:
            text: string to extract entities from

        Returns:
            A tuple of two lists with first list containing the detected budgets and second list containing their
            corresponding substrings in the original message.

            For example:

                ([{'max_budget': 1000, 'type': 'normal_budget', 'min_budget': 0}], ['rs. 1000'])

            Additionally this function assigns these lists to self.budget and self.original_budget_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text.lower()
        self.tagged_text = self.text
        self.budget, self.original_budget_text = self._detect_budget()
        return self.budget, self.original_budget_text

    @property
    def supported_languages(self):
        return self._supported_languages

    def _detect_budget(self):
        """Detects budget in the self.text

        Returns:
            A tuple of two lists with first list containing the detected budgets and second list containing their
            corresponding substrings in the original message.

            For example:
                input: "shirts between 2000 to 3000"
                output: ([{'max_budget': 3000, 'type': 'normal_budget', 'min_budget': 2000}], ['2000 to 3000'])

        """

        budget_list = []
        original_list = []
        budget_list, original_list = self._detect_min_max_budget(budget_list, original_list)
        self._update_processed_text(original_list)
        budget_list, original_list = self._detect_min_budget(budget_list, original_list)
        self._update_processed_text(original_list)
        budget_list, original_list = self._detect_max_budget(budget_list, original_list)
        self._update_processed_text(original_list)
        budget_list, original_list = self._detect_any_budget(budget_list, original_list)
        self._update_processed_text(original_list)
        if not budget_list and self._use_text_detection:
            budget_list, original_list = self._detect_text_budget(budget_list, original_list)
            self._update_processed_text(original_list)

        return budget_list, original_list

    def _detect_min_budget(self, budget_list=None, original_list=None):
        """Detects minimum budget from text using regex
        This is a function which will be called when we want to detect the budget using regex from the text

        Returns:
            A tuple of two lists with first list containing the detected budget and second list containing their
            corresponding substrings in the original message.

            For example:
                input: "tshirts greater than 2k"
                output: ([{'max_budget': 0, 'type': 'normal_budget', 'min_budget': 2000}], ['greater than 2k'])

        """

        if budget_list is None:
            budget_list = []
        if original_list is None:
            original_list = []
        pattern = re.compile(r'\s('
                             r'(?:above|more? than|more?|at ?least|greater than|greater|abv|abov|more? den|\>\s*\=?)'
                             r'\s+' +
                             self._budget_pattern +
                             r')(?:\b|\.|\s)', flags=re.UNICODE | re.IGNORECASE)

        for match in pattern.finditer(self.processed_text):
            original, amount, unit = match.groups()
            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }

            scale = self.get_scale(unit)

            if amount.replace(',', '').replace('.', '').isdigit():
                amount = float(amount.replace(',', '')) * scale

                amount = int(amount)  # casting to int for backward compatibility
                if self.min_digit <= len(str(amount)) <= self.max_digit:
                    budget['min_budget'] = amount
                    budget_list.append(budget)
                    original_list.append(original.strip())

        return budget_list, original_list

    def _detect_max_budget(self, budget_list=None, original_list=None):
        """Detects maximum budget from text using regex
        This is a function which will be called when we want to detect the budget using regex from the text

        Returns:
            A tuple of two lists with first list containing the detected budget and second list containing their
            corresponding substrings in the original message.

            For example:
                input: "tshirts less than 2k"
                output: ([{'max_budget': 2000, 'type': 'normal_budget', 'min_budget': }], ['less than 2k'])

        """

        if budget_list is None:
            budget_list = []
        if original_list is None:
            original_list = []

        pattern = re.compile(r'\s('
                             r'(?:max|upto|o?nly|around|below|at ?most|less than|less|less den|\<\s*\=?)'
                             r'\s+' +
                             self._budget_pattern +
                             r')(?:\b|\.|\s)', flags=re.UNICODE | re.IGNORECASE)

        for match in pattern.finditer(self.processed_text):
            original, amount, unit = match.groups()

            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }

            scale = self.get_scale(unit)

            if amount.replace(',', '').replace('.', '').isdigit():
                amount = float(amount.replace(',', '')) * scale

                amount = int(amount)  # casting to int for backward compatibility
                if self.min_digit <= len(str(amount)) <= self.max_digit:
                    budget['max_budget'] = amount
                    budget_list.append(budget)
                    original_list.append(original.strip())

        return budget_list, original_list

    def _detect_min_max_budget(self, budget_list=None, original_list=None):
        """Detects both minimum and maximum budget from text using regex
        This is a function which will be called when we want to detect the budget using regex from the text

        Returns:
            A tuple of two lists with first list containing the detected budget and second list containing their
            corresponding substrings in the original message.

            For example:
                input: shirts between 2000 to 3000
                output: ([{'max_budget': 3000, 'type': 'normal_budget', 'min_budget': 2000}], ['2000 to 3000'])

        """
        if budget_list is None:
            budget_list = []
        if original_list is None:
            original_list = []

        pattern = re.compile(r'\s(' +
                             self._budget_pattern +
                             r'\s*(?:\-|to|and|till)\s*' +
                             self._budget_pattern +
                             r')(?:\b|\.|\s)', flags=re.UNICODE | re.IGNORECASE)

        for match in pattern.finditer(self.processed_text):
            original, min_budget, min_unit, max_budget, max_unit = match.groups()

            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }

            min_budget_scale = self.get_scale(min_unit)
            max_budget_scale = self.get_scale(max_unit)

            if min_budget.replace(',', '').replace('.', '').isdigit():
                min_budget = float(min_budget.replace(',', '')) * min_budget_scale
            else:
                min_budget = 0

            if max_budget.replace(',', '').replace('.', '').isdigit():
                max_budget = float(max_budget.replace(',', '')) * max_budget_scale
            else:
                max_budget = 0

            min_budget = int(min_budget)
            max_budget = int(max_budget)

            min_budget = min_budget if self.min_digit <= len(str(min_budget)) <= self.max_digit else 0
            max_budget = max_budget if self.min_digit <= len(str(max_budget)) <= self.max_digit else 0

            if min_budget != 0 and max_budget != 0 and min_budget <= max_budget:
                budget['min_budget'] = min_budget
                budget['max_budget'] = max_budget
                budget_list.append(budget)
                original_list.append(original.strip())

        return budget_list, original_list

    def _detect_any_budget(self, budget_list=None, original_list=None):
        """Detects a budget from text using regex
        This is a function which will be called when we want to detect the budget using regex from the text

        Returns:
            A tuple of two lists with first list containing the detected budget and second list containing their
            corresponding substrings in the original message.

            For example:
                input: shirts between 2000 to 3000
                output: ([{'max_budget': 3000, 'type': 'normal_budget', 'min_budget': 2000}], ['2000 to 3000'])

        """

        if budget_list is None:
            budget_list = []
        if original_list is None:
            original_list = []

        pattern = re.compile(r'\s(' +
                             self._budget_pattern +
                             r')(?:\b|\.|\s)', flags=re.UNICODE | re.IGNORECASE)

        for match in pattern.finditer(self.processed_text):
            original, amount, unit = match.groups()
            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }

            scale = self.get_scale(unit)

            if amount.replace(',', '').replace('.', '').isdigit():
                amount = float(amount.replace(',', '')) * scale

                amount = int(amount)  # casting to int for backward compatibility

                if self.min_digit <= len(str(amount)) <= self.max_digit:
                    budget['max_budget'] = amount
                    budget_list.append(budget)
                    original_list.append(original.strip())

        return budget_list, original_list

    def _detect_text_budget(self, budget_list=None, original_list=None):
        """Detects budget  from text using text detection logic i.e.TextDetector
        This is a function which will be called when we want to detect the budget using text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

        """
        if budget_list is None:
            budget_list = []
        if original_list is None:
            original_list = []

        text_detection_object = TextDetector(entity_name=self.entity_name)

        budget_text_list, original_text_list = text_detection_object.detect_entity(self.text, return_str=True)
        # FIXME: Broken/Ineffective code.
        self.tagged_text = text_detection_object.tagged_text
        self.processed_text = text_detection_object.processed_text
        for _, original_text in zip(budget_text_list, original_text_list):
            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_TEXT
            }

            budget_list.append(budget)
            original_list.append(original_text)

        return budget_list, original_list

    def _update_processed_text(self, original_budget_strings):
        """
        Replaces detected budgets with self.tag generated from entity_name used to initialize the object with

        A final string with all budgets replaced will be stored in self.tagged_text attribute
        A string with all budgets removed will be stored in self.processed_text attribute

        Args:
            original_budget_strings: list of substrings of original text to be replaced with self.tag
        """
        for detected_text in original_budget_strings:
            if detected_text:
                self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
                self.processed_text = self.processed_text.replace(detected_text, '')

    def set_min_max_digits(self, min_digit, max_digit):
        """
        Update min max digit

        Args:
            min_digit (int): min digit
            max_digit (int): max digit
        """
        self.min_digit = min_digit
        self.max_digit = max_digit
