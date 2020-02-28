from __future__ import absolute_import
import re
from ner_v1.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG


class EmailDetector(BaseDetector):
    """Detects email addresses in given text and tags them.

    Detects all email addresses in given text and replaces them by entity_name

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected email addresses would be replaced with on calling detect_entity()
        tagged_text: string with email addresses replaced with tag defined by entity name
        processed_text: string with email addresses detected removed
        email: list of email addresses detected
        original_email_text: list to store substrings of the text detected as email addresses
        tag: entity_name prepended and appended with '__'

    For Example:
        text = "Hey can you send my boarding pass to example@haptik.ai ?"
        email_detector = EmailDetector("email_address")
        emails, original_emails = email_detector.detect_entity(text)
        email_detector.tagged_text

            Output:
                 ' Hey can you send my boarding pass to __email_address__ ? '

        emails, original_emails

            Output:
                (['example@haptik.ai'], ['example@haptik.ai'])

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False):
        """Initializes a EmailDetector object

        Args:
           entity_name: A string by which the detected email addresses would be replaced with on
                       calling detect_entity()
           source_language_script: ISO 639 code for language of entities to be detected by the instance of this class
           translation_enabled: True if messages needs to be translated in case detector does not support a
                                particular language, else False

        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(EmailDetector, self).__init__(source_language_script, translation_enabled)

        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.email = []
        self.original_email_text = []
        self.tag = '__' + self.entity_name + '__'

    @property
    def supported_languages(self):
        return self._supported_languages

    def _detect_email(self):
        """Detects email addresses in the self.text

        This function is called by detect_entity(text)

        Returns:
            A tuple of two lists with first list containing the detected email addresses and second list containing
            their corresponding substrings in the given text.

            For example:
                (['example@haptik.ai'], ['example@haptik.ai'])

        """
        email_list = []
        original_list = []
        email_list, original_list = self._detect_email_format(email_list, original_list)
        self._update_processed_text(original_list)

        return email_list, original_list

    def detect_entity(self, text, **kwargs):
        """Detects email addresses in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future

        Returns:
            A tuple of two lists with first list containing the detected email addresses and second list containing
            their corresponding substrings in the given text.

            For example:
                (['example@haptik.ai'], ['example@haptik.ai'])

            Additionally this function assigns these lists to self.email and self.original_email_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        email_data = self._detect_email()
        self.email = email_data[0]
        self.original_email_text = email_data[1]
        return email_data

    def _detect_email_format(self, email_list=None, original_list=None):
        """Detects email addresses from self.text conforming to formats defined by regex pattern.

        This function is called by _detect_email()

        Args:
            email_list: Optional, list to store detected email addresses
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            email addresses

        Returns:
            A tuple of two lists with first list containing the detected email addresses and second list containing
            their corresponding substrings in the given text.

            For example:
                (['example@haptik.ai'], ['example@haptik.ai'])
        """
        if email_list is None:
            email_list = []
        if original_list is None:
            original_list = []

        regex_string = r'(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+)*|' + \
                       r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")' + \
                       r'@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|' + \
                       r'\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|' + \
                       r'[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|' + \
                       r'\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'

        patterns = re.findall(regex_string, self.processed_text.lower())
        for pattern in patterns:
            original = pattern
            email = pattern
            email_list.append(email)
            original_list.append(original)
        return email_list, original_list

    def _update_processed_text(self, original_email_strings):
        """
        Replaces detected email addresses with tag generated from entity_name used to initialize the object with

        A final string with all email addresses replaced will be stored in object's tagged_text attribute
        A string with all email addresses removed will be stored in object's processed_text attribute

        Args:
            original_email_strings: list of substrings of original text to be replaced with tag created
                                    from entity_name
        """
        for detected_text in original_email_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
