from __future__ import absolute_import
import re
from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG


class ShoppingSizeDetector(BaseDetector):
    """Detects size which are used for shopping from the text  and tags them.

    Detects the sizes from the text and replaces them by entity_name.
    This detection logic will first check if text contains size in textual format (i.e. Large, XL, X-Large, etc)
    for this we call TextDetector class and then we have regex that will identify integer from the text

    For Example:

        size_detector = ShoppingSizeDetector("shopping_clothes_size")
        message = "Suggest me Medium size tshirt and jeans of 34 waist"
        size, original_numbers = size_detector.detect_entity(message)
        tagged_text = size_detector.tagged_text
        print size, ' -- ', original_numbers
        print 'Tagged text: ', tagged_text

         >> ['M','34'] -- ['Medium','34']
            Tagged text: Suggest me __shopping_size__ size tshirt and jeans of __shopping_size__ waist



    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected size would be replaced with on calling detect_entity()
        This is constant and its value is size_detector
        tagged_text: string with size replaced with tag defined by entity name
        processed_text: string with sizes detected removed
        size: list of sizes detected
        original_size_text: list to store substrings of the text detected as size
        tag: entity_name prepended and appended with '__'

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)
    """

    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False):
        """Initializes a ShoppingSizeDetector object

        Args:
            entity_name: A string by which the detected numbers would be replaced with on calling detect_entity()
            source_language_script: ISO 639 code for language of entities to be detected by the instance of this class
            translation_enabled: True if messages needs to be translated in case detector does not support a
                                 particular language, else False
        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(ShoppingSizeDetector, self).__init__(source_language_script, translation_enabled)
        self.entity_name = entity_name
        self.text = ''
        self.text_dict = {}
        self.tagged_text = ''
        self.processed_text = ''
        self.size = []
        self.original_size_text = []
        self.text_detection_object = TextDetector(entity_name=self.entity_name)
        self.tag = '__' + self.entity_name + '__'

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        """Detects size in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:
            A tuple of two lists with first list containing the detected sizes and second list containing their
            corresponding substrings in the original message.

            For example:

                (['XL','M','30'], [''X-Large','Medium','30'])

            Additionally this function assigns these lists to self.size and self.original_size_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text

        size_data = self._detect_size()
        self.size = size_data[0]
        self.original_size_text = size_data[1]
        return size_data

    def _detect_size(self):
        """Detects size in the self.text

        Returns:
            A tuple of two lists with first list containing the detected sizes and second list containing their
            corresponding substrings in the original message.

            For example:
                input: Show me X-Large and Medium size tshirt and jeans of waist 34
                output: (['XL','M', 34], ['X-Large', 'Medium', 34])

        """
        size_list = []
        original_list = []
        size_list, original_list = self._detect_size_from_text(size_list, original_list)
        self._update_processed_text(original_list)

        size_list, original_list = self._detect_size_from_regex(size_list, original_list)
        self._update_processed_text(original_list)
        return size_list, original_list

    def _detect_size_from_text(self, size_list=None, original_list=None):
        """Detects any size  from text using text detection logic i.e.TextDetector
        This is a function which will be called when we want to detect the size using text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                input: "Suggest me shirt of size X-Large"
                output: (['XL'], ['X-Large'])

        """
        if size_list is None:
            size_list = []
        if original_list is None:
            original_list = []

        size_list, original_list = self.text_detection_object.detect_entity(self.text, return_str=True)
        self.tagged_text = self.text_detection_object.tagged_text
        self.processed_text = self.text_detection_object.processed_text
        return size_list, original_list

    def _detect_size_from_regex(self, size_list=None, original_list=None):
        """Detects any size  from text using regex
        This is a function which will be called when we want to detect the size using regex from the text

        Returns:
            A tuple of two lists with first list containing the detected numbers and second list containing their
            corresponding substrings in the original message.

            For example:
                input: "Suggest me shirt of size 30"
                output: (['30'], ['30'])

        """

        if size_list is None:
            size_list = []
        if original_list is None:
            original_list = []

        pattern = re.search(r'(\s\d{1,2}\s)', self.processed_text.lower())
        if pattern:
            size_list.append(pattern.group(0).strip())
            original_list.append(pattern.group(0).strip())
        return size_list, original_list

    def _update_processed_text(self, original_size_strings):
        """
        Replaces detected sizes with self.tag generated from entity_name used to initialize the object with

        A final string with all sizes replaced will be stored in self.tagged_text attribute
        A string with all sizes removed will be stored in self.processed_text attribute

        Args:
            original_size_strings: list of substrings of original text to be replaced with self.tag
        """
        for detected_text in original_size_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
