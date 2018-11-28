# coding=utf-8
import pandas as pd

from ner_v2.constant import NUMBER_DATA_FILE_NUMBER, NUMBER_DATA_FILE_NUMERALS, NUMBER_DATA_FILE_VALUE, \
    NUMBER_TYPE_UNIT, NUMBER_DATA_FILE_TYPE, NUMBER_DIGIT_UNITS


class BaseNumberDetector(object):
    def __init__(self, entity_name, data_directory_path):
        """
        Base Regex class which will be imported by language date class by giving their data folder path
        This will create standard regex and their parser to detect date for given language.
        Args:
            data_directory_path (str): path of data folder for given language
        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'
        self.numbers_word = None
        self.language_number_map = None

        # Method to initialise value in regex
        self.init_regex_and_parser(data_directory_path)

        # Variable to define default order in which detector will work
        self.detector_preferences = [self._detect_number_from_numerals,
                                     self._detect_numeric_digit]

    def detect_time(self, text):
        self.text = text
        self.processed_text = text
        self.tagged_text = text

        number_list, original_list = None, None
        for detector in self.detector_preferences:
            number_list, original_list = detector(number_list, original_list)
            self._update_processed_text(original_list)
        return number_list, original_list

    @staticmethod
    def _get_numerals_list(numerals_text):
        """
        Split numerals
        Args:
            numerals_text (str): numerals text
        Returns:
            (list) : list containing numeral after split
        """
        numerals_list = numerals_text.split("|")
        return [num.strip() for num in numerals_list if num.strip()]

    def init_regex_and_parser(self, data_directory_path):
        """
        Initialise numbers word from from data file
        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        data_df = pd.read_csv(data_directory_path)
        for index, row in data_df.iterrows():
            if row[NUMBER_DATA_FILE_VALUE] in NUMBER_DIGIT_UNITS:
                self.language_number_map[row[NUMBER_DATA_FILE_NUMBER]] = row[NUMBER_DATA_FILE_VALUE]
                self.language_number_map[str(row[NUMBER_DATA_FILE_VALUE])] = row[NUMBER_DATA_FILE_VALUE]

            numerals_list = self._get_numerals_list(row[NUMBER_DATA_FILE_NUMERALS])
            if row[NUMBER_DATA_FILE_TYPE] == NUMBER_TYPE_UNIT:
                self.numbers_word[row[NUMBER_DATA_FILE_NUMBER]] = (1, row[NUMBER_DATA_FILE_VALUE])
                for each in numerals_list:
                    self.numbers_word[each] = (1, row[NUMBER_DATA_FILE_VALUE])
            else:
                self.numbers_word[row[NUMBER_DATA_FILE_NUMBER]] = (row[NUMBER_DATA_FILE_VALUE], 0)
                for each in numerals_list:
                    self.numbers_word[each] = (row[NUMBER_DATA_FILE_VALUE], 0)

    def _detect_number_from_numerals(self, number_list, original_list):
        number_list = number_list or []
        original_list = original_list or []

        current = result = 0
        current_text, result_text = '', ''
        on_number = False
        for word in self.processed_text.split():
            if word not in self.numbers_word:
                if on_number:
                    original = result_text.strip() + " " + current_text.strip()
                    number_list.append(repr(result + current))
                    original_list.append(original)

                result = current = 0
                result_text, current_text = '', ''
                on_number = False
            else:
                scale, increment = self.numbers_word[word]
                current = current * scale + increment
                current_text += word + " "
                if scale > 100:
                    result += current
                    result_text += current_text + " "
                    current = 0
                    current_text = ''
                on_number = True

        if on_number:
            original = result_text.strip() + " " + current_text.strip()
            number_list.append(repr(result + current))
            original_list.append(original)

        return number_list, original_list

    def _detect_numeric_digit(self, number_list, original_list):
        number_list = number_list or []
        original_list = original_list or []

        for word in self.processed_text.split():
            word_chars = list(word)
            if not (set(word_chars) - set(self.language_number_map.keys())):
                number = [str(self.language_number_map[ch]) for ch in word_chars]
                number_list.append(number)
                original_list.append(word)

        return number_list, original_list

    def _update_processed_text(self, original_date_list):
        """
        Replaces detected date with tag generated from entity_name used to initialize the object with

        A final string with all dates replaced will be stored in object's tagged_text attribute
        A string with all dates removed will be stored in object's processed_text attribute

        Args:
            original_date_list (list): list of substrings of original text to be replaced with tag
                                       created from entity_name
        """
        for detected_text in original_date_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')


class NumberDetector(BaseNumberDetector):
    def __init__(self, entity_name, data_directory_path):
        super(NumberDetector, self).__init__(entity_name=entity_name, data_directory_path=data_directory_path)
