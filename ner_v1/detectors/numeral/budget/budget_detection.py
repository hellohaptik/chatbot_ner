import re

from ner_v1.detectors.constant import BUDGET_TYPE_NORMAL, BUDGET_TYPE_TEXT
from lib.nlp.regexreplace import RegexReplace
from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.detectors.base_detector import BaseDetector
from ner_v1.language_utilities.constant import ENGLISH_LANG


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
        regex_object: regex object that is used to substitute k with 000 i.e. if text contains 2k then
        it will be substituted as 2000
        text_detection_object: text detection object to detect text in Textual format
        
    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)

    """

    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False):
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
        self.unit_present_list = ['k', 'l', 'm', 'c', 'h', 'th']
        regx_for_units = [(r'([\d,.]+)\s*k', 1000),
                          (r'([\d,.]+)\s*h', 1000),
                          (r'([\d,.]+)\s*th', 1000),
                          (r'([\d,.]+)\s*l', 100000),
                          (r'([\d,.]+)\s*lacs?', 100000),
                          (r'([\d,.]+)\s*lakh?', 100000),
                          (r'([\d,.]+)\s*lakhs?', 100000),
                          (r'([\d,.]+)\s*m', 1000000),
                          (r'([\d,.]+)\s*million', 1000000),
                          (r'([\d,.]+)\s*mill?', 1000000),
                          (r'([\d,.]+)\s*c', 10000000),
                          (r'([\d,.]+)\s*cro?', 10000000),
                          (r'([\d,.]+)\s*crore?', 10000000),
                          (r'([\d,.]+)\s*crores?', 10000000)]
        self.regex_object = RegexReplace(regx_for_units)
        self.tag = '__' + self.entity_name + '__'
        self.text_detection_object = TextDetector(entity_name=entity_name)

    def detect_entity(self, text):
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
        budget_data = self._detect_budget()
        self.budget = budget_data[0]
        self.original_budget_text = budget_data[1]
        return budget_data

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
        if not budget_list:
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
        patterns = re.findall(
            r'(\s(above|more? than|more?|greater than|greater|abv|abov|more? den|\>\s*\=?)\s+'
            r'(rs.|rs|rupees|rupee)*\s*([\d.,]+\s*[klmct]?[a-z]*|[\d.,]+\s*[klmct]?[a-z]*)\s*'
            r'(rs.|rs|rupees|rupee|\.)?\s)', self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()
            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }

            if any([unit in pattern[3] for unit in self.unit_present_list]):
                replace_comma = re.sub(',', '', pattern[3])
                amount = int(self.regex_object.unit_substitute(replace_comma))
            else:
                replace_comma = re.sub(',', '', pattern[3])
                amount = int(replace_comma)

            if self.min_digit <= len(str(amount)) <= self.max_digit:
                budget['min_budget'] = amount
                budget_list.append(budget)
                original_list.append(original)

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

        patterns = re.findall(
            r'(\s(max|upto|o?nly|around|below|less than|less|less den|\<\s*\=?)\s+(rs.|rs|rupees|rupee)'
            r'?\s*([\d.,]+\s*[klmct]?[a-z]*|[\d.,]+\s*[klmct]?[a-z]*)\s*(rs.|rs|rupees|rupee|\.)?\s)',
            self.processed_text.lower())
        for pattern in patterns:
            original = pattern[0].strip()

            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }

            if any([unit in pattern[3] for unit in self.unit_present_list]):
                comma_removed_unit_text = pattern[3].replace(',', '')
                amount = int(self.regex_object.unit_substitute(comma_removed_unit_text))
            else:
                comma_removed_number = pattern[3].replace(',', '')
                amount = int(comma_removed_number)

            if self.min_digit <= len(str(amount)) <= self.max_digit:
                budget['max_budget'] = amount
                budget_list.append(budget)
                original_list.append(original)

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

        patterns = re.findall(r'(\s(([\d,.]+\s*[klmct]?[a-z]*)|([\d,.]+\s*[klmct]?[a-z]*))\s*(\-|to|and)\s*'
                              r'(([\d,.]+\s*[klmct]?[a-z]*)|([\d,.]+\s*[klmct]?[a-z]*))\.?\s)',
                              self.processed_text.lower())
        for pattern in patterns:
            original = None
            pattern = list(pattern)
            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }

            flag_contains_k = False
            max_budget = 0
            min_budget = 0
            _min_budget = 0
            if pattern[6]:
                if any([unit in pattern[6] for unit in self.unit_present_list]):
                    flag_contains_k = True
                else:
                    flag_contains_k = False
                comma_removed_unit_text = pattern[6].replace(',', '')
                max_budget = int(self.regex_object.unit_substitute(comma_removed_unit_text))
            elif pattern[7]:
                comma_removed_number = pattern[7].replace(',', '')
                max_budget = int(comma_removed_number)
                min_budget = 0

            if pattern[2]:
                _comma_removed_unit_text = pattern[2].replace(',', '')
                _min_budget = int(self.regex_object.unit_substitute(_comma_removed_unit_text))
                if flag_contains_k:
                    for u in self.unit_present_list:
                        if u in pattern[6]:
                            pattern[2] = str(pattern[2]).strip() + u
                            break
                comma_removed_unit_text = pattern[2].replace(',', '')
                min_budget = int(self.regex_object.unit_substitute(comma_removed_unit_text))
            elif pattern[3]:
                comma_removed_number = pattern[3].replace(',', '')
                min_budget = int(comma_removed_number)
            if min_budget > max_budget:
                min_budget = _min_budget
            min_budget = min_budget if self.min_digit <= len(str(min_budget)) <= self.max_digit else 0
            max_budget = max_budget if self.min_digit <= len(str(max_budget)) <= self.max_digit else 0
            if min_budget != 0 and max_budget != 0 and min_budget <= max_budget:
                original = pattern[0].strip()
                budget['min_budget'] = min_budget
                budget['max_budget'] = max_budget

                budget_list.append(budget)
                original_list.append(original)
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

        text = self.processed_text.lower().strip()

        units_patterns = [r'k|hazaa?r|haja?ar|thousand', r'l|lacs?|lakh?|lakhs?',
                          r'm|million|mill?', r'cro?|cror?|crore?|crores?']
        units_order = [1e3, 1e5, 1e6, 1e7]
        full = re.compile(r'((rs.|rs|rupees|rupee)?\s*((\d+((\,|\.)\d+)+)|(0|[1-9]\d*)?(\.\d+)?(?<=\d))'
                          r'\s*(' + r'|'.join(units_patterns) + r')?\s*(rs.|rs|rupees|rupee)?)\b')
        units_patterns = map(lambda s: '^' + s, units_patterns)
        units_patterns = map(re.compile, units_patterns)
        matches = full.findall(text)
        for match in matches:
            original = match[0].strip()
            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_NORMAL
            }
            amount, unit = match[2], match[-2]
            if not amount:
                continue
            amount = amount.replace(',', '')
            _amount = amount.split('.')
            if len(_amount) > 1:
                amount = ''.join(_amount[:-1]) + '.' + _amount[-1]
            amount = float(amount)
            for i, pattern in enumerate(units_patterns):
                if pattern.findall(unit):
                    amount = int(amount * units_order[i])
                    break
            amount = int(amount)
            if self.min_digit <= len(str(amount)) <= self.max_digit:
                budget['max_budget'] = amount
                budget_list.append(budget)
                original_list.append(original)

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

        budget_entity_verified_values, original_text_list = self.text_detection_object.detect_entity(self.text)
        budget_text_list = TextDetector.get_text_entity_values(text_entity_verified_values=budget_entity_verified_values)
        self.tagged_text = self.text_detection_object.tagged_text
        self.processed_text = self.text_detection_object.processed_text
        count = 0
        while count < len(original_text_list):
            budget = {
                'min_budget': 0,
                'max_budget': 0,
                'type': BUDGET_TYPE_TEXT
            }

            budget_list.append(budget)
            count += 1

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
