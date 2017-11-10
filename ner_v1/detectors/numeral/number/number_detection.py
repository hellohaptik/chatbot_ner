import re


class NumberDetector(object):
    """Detects number from the text  and tags them.

    Detects all numbers in given text and replaces them by entity_name

    For Example:

        number_detector = NumberDetector("number_of_units")
        message = "I want to purchase 30 units of mobile and 40 units of Television"
        numbers, original_numbers = number_detector.detect_entity(message)
        tagged_text = number_detector.tagged_text
        print numbers, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> ['30', '40'] -- ['30', '40']
            Tagged text: I want to purchase 30 units of mobile and 40 units of Television'


        number_detector = NumberDetector("number_of_people")
        message = "Can you please help me to book tickets for 3 people"
        numbers, original_numbers = number_detector.detect_entity(message)
        tagged_text = number_detector.tagged_text

        print numbers, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> ['3'] -- ['for 3 people']
            Tagged text: Can you please help me to book tickets __number_of_people__

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected number would be replaced with on calling detect_entity()

        tagged_text: string with numbers replaced with tag defined by entity name
        processed_text: string with numbers detected removed
        number: list of numbers detected
        original_number_text: list to store substrings of the text detected as numbers
        tag: entity_name prepended and appended with '__'

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
        Currently, there are two detection logics for detecting numbers from text one to detect number of people
        and other any number. If we want detect number of people entity_name should be set to 'number_of_people'
        else any name can be passed as entity_name.
        We can detect numbers from 1 digit to 3 digit.
    """
    def __init__(self, entity_name):
        """Initializes a NumberDetector object

        Args:
            entity_name: A string by which the detected numbers would be replaced with on calling detect_entity()
        """
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.number = []
        self.original_number_text = []
        self.tag = '__' + self.entity_name + '__'
        self.task_dict = {
            'number_of_people': self._detect_number_of_people_format,
            'Default': self._detect_number_format
        }

    def detect_entity(self, text):
        """Detects numbers in the text string

        Args:
            text: string to extract entities from

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:

                (['3'], ['3 people'])

            Additionally this function assigns these lists to self.number and self.original_number_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        number_data = self._detect_number()
        self.number = number_data[0]
        self.original_number_text = number_data[1]
        return number_data

    def _detect_number(self):
        """Detects numbers in the self.text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                (['3'], ['for 3 people'])

        """
        number_list, original_list = self.task_dict.get(self.entity_name, self.task_dict['Default'])()
        self._update_processed_text(original_list)
        return number_list, original_list

    def _detect_number_format(self):
        """Detects any numbers from text
        This is a default function which will be called when we want to detect the number from the text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                input: "I want to purchase 30 units of mobile and 40 units of Television"
                output: (['30', '40'], ['30','40'])

        Note: Currently,we can detect numbers from 1 digit to 3 digit
        """
        number_list = []
        original_list = []
        patterns = re.findall(r'\s([0-9]{1,3})[\s|,]', self.processed_text.lower())
        for pattern in patterns:
            number_list.append(pattern)
            original_list.append(pattern)
        return number_list, original_list

    def _detect_number_of_people_format(self):
        """Detects any numbers from text
        This is a function which will be called when we want to detect the number of persons from the text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                input text: "Can you please help me to book tickets for 3 people"
                output: (['3'], ['for 3 people'])

        Note: Currently, we can detect numbers from 1 digit to 3 digit. This function will be enabled only
        if entity_name is set to  'number_of_people'
        """
        number_list = []
        original_list = []
        patterns = re.findall(r'\s((fo?r)*\s*([0-9]{1,3})\s*(ppl|people|passengers?|travellers?|persons?|pax|adults?)'
                              r'*)\s', self.processed_text.lower())
        for pattern in patterns:
            number_list.append(pattern[2])
            original_list.append(pattern[0])
        return number_list, original_list

    def _update_processed_text(self, original_number_strings):
        """
        Replaces detected numbers with self.tag generated from entity_name used to initialize the object with

        A final string with all numbers replaced will be stored in self.tagged_text attribute
        A string with all numbers removed will be stored in self.processed_text attribute

        Args:
            original_number_strings: list of substrings of original text to be replaced with self.tag
        """
        for detected_text in original_number_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')


