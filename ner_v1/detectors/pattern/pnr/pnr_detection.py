from __future__ import absolute_import
import re
from ner_v1.detectors.base_detector import BaseDetector
from language_utilities.constant import ENGLISH_LANG


class PNRDetector(BaseDetector):
    """Detects PNR (serial) codes (Passenger Record Number, usually present with train or flight bookings) in given text
     and tags them. Usually flight pnr codes are 5 to 8 characters long.

    Detects all PNR/serial codes of variable length about 5 to 20 characters in given text and replaces them by
    entity_name. Different detectors are used depending on the entity_name used to initialize the PNRDetector object.
    A task_dict, a dictonary mapping detector functions to entity_name is used for this.
    For example if 'train_pnr' is used to initialize PNRDetector(),
    _detect_railway_pnr() would be called to detect pnr codes. In case if entity_name is not present in
    task_dict , _detect_serial_pnr() is used to detect pnr codes.

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected pnr codes would be replaced with on calling detect_entity()
        tagged_text: string with pnr codes replaced with tag defined by entity name
        processed_text: string with pnr codes detected removed
        pnr_list: list of pnr codes detected
        original_pnr_text: list to store substrings of the text detected as pnr codes
        tag: entity_name prepended and appended with '__'
        task_dict : A dictonary mapping detector functions to entity_name. For example if 'train_pnr' is used to
                    initialize PNRDetector(), _detect_railway_pnr() would be called to detect pnr codes
                    In case if entity_name is not present in task_dict , _detect_serial_pnr() is used to detect pnr
                    codes

    For Example:
        text = "Your flight booking was sucessful. Your pnr is 4sgx3e."
        pnr_detector = PNRDetector("pnr_number")
        pnr_numbers, original_pnr_numbers = pnr_detector.detect_entity(text)
        pnr_detector.tagged_text

            Output:
               ' Your flight booking was sucessful. Your pnr is __pnr__number__. '

        pnr_numbers, original_pnr_numbers

            Output:
                (['4sgx3e'], ['4sgx3e'])

    Note:
        text and tagged_text will have a extra space prepended and appended after calling detect_entity(text)

    More Examples:

        text = "Your flight booking was sucessful. Your pnr is 43333."
        ...
        pnr_numbers, original_pnr_numbers
            (['43333'], ['43333'])

        text = "Your flight booking was sucessful. Your pnr is 433."
        ...
        pnr_numbers, original_pnr_numbers
            ([], [])

        text = "Your flight booking was sucessful. Your pnr is sgxsgx."
        ...
        pnr_numbers, original_pnr_numbers
            (['sgxsgx'], ['sgxsgx'])
    """

    def __init__(self, entity_name, source_language_script=ENGLISH_LANG, translation_enabled=False):
        """Initializes a PNRDetector object

        Args:
            entity_name: A string by which the detected pnr codes would be replaced with on calling detect_entity()
            source_language_script: ISO 639 code for language of entities to be detected by the instance of this class
            translation_enabled: True if messages needs to be translated in case detector does not support a
                                 particular language, else False
        """
        # assigning values to superclass attributes
        self._supported_languages = [ENGLISH_LANG]
        super(PNRDetector, self).__init__(source_language_script, translation_enabled)

        self.entity_name = entity_name
        self.task_dict = {
            'train_pnr': self._detect_railway_pnr,
            'Default': self._detect_serial_pnr
        }
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.pnr_list = []
        self.original_pnr_text = []
        self.tag = '__' + self.entity_name + '__'

    @property
    def supported_languages(self):
        return self._supported_languages

    def detect_entity(self, text, **kwargs):
        """Detects pnr codes in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future

        Returns:
            A tuple of two lists with first list containing the detected pnr codes and second list containing their
            corresponding substrings in the given text.

            For example:

                (['4sgx3e'], ['4sgx3e'])

            Additionally this function assigns these lists to self.pnr_list and self.original_pnr_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        pnr_data = self.task_dict.get(self.entity_name, self.task_dict['Default'])()
        self.pnr_list = pnr_data[0]
        self.original_pnr_text = pnr_data[1]
        return pnr_data

    def _detect_railway_pnr(self):
        """Detects railway pnr codes in the text string

        Detects Indian Railways 10 to 12 digits PNR codes in the text

        Returns:
           A tuple of two lists with first list containing the detected pnr codes and second list containing their
           corresponding substrings in the given text.

           For example, if text is "My train pnr is 2459547855, can you check the train status for me ?"
           It returns

               (['2459547855'], ['2459547855'])

           Additionally this function assigns these lists to self.pnr_list and self.original_original_pnr_text
           attributes respectively.

        """
        # print 'detection for default task'
        railway_pnr_list = []
        original_list = []

        railway_pnr_list, original_list = self._detect_railway_pnr_format(railway_pnr_list, original_list)
        self._update_processed_text(original_list)
        railway_pnr_list, original_list = self._detect_railway_pnr_long_format(railway_pnr_list, original_list)
        self._update_processed_text(original_list)
        return railway_pnr_list, original_list

    def _detect_railway_pnr_format(self, railway_pnr_list=None, original_list=None):
        """
        Detects Indian Railways 10 to 12 digits pnr codes from self.text conforming to formats defined by
         regex pattern.

        This function is called by _detect_railway_pnr()

        Args:
            railway_pnr_list: Optional, list to store detected pnr codeses
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            pnr codeses

        Returns:
            A tuple of two lists with first list containing the detected pnr codeses and second list containing
            their corresponding substrings in the given text.

            For example:
                (['2459547855'], ['2459547855'])
        """
        if railway_pnr_list is None:
            railway_pnr_list = []
        if original_list is None:
            original_list = []

        patterns = re.findall(r'\b([0-9]{10,12})\b', self.processed_text.lower())
        for pattern in patterns:
            railway_pnr_list.append(pattern)
            original_list.append(pattern)
        return railway_pnr_list, original_list

    def _detect_railway_pnr_long_format(self, railway_pnr_list=None, original_list=None):
        """
        Detects railway PNR 10 digit number with special characters

        Args:
            railway_pnr_list: Optional, list to store detected pnr codeses
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            pnr codeses
        Returns:
            A tuple of two lists with first list containing the detected pnr codeses and second list containing
            their corresponding substrings in the given text.

            For example:
                (['2459547855'], ['2459547855'])
        """
        if railway_pnr_list is None:
            railway_pnr_list = []
        if original_list is None:
            original_list = []

        patterns = re.findall(r'\b([0-9\-\s\(\)\.]{10,20})\b', self.processed_text.lower())
        for pattern in patterns:
            clean_pnr = self._clean_pnr(pattern)
            if len(clean_pnr) == 10:
                railway_pnr_list.append(clean_pnr)
                original_list.append(pattern)
        return railway_pnr_list, original_list

    def _clean_pnr(self, pnr):
        """
        This function clean special character from pnr text

        Args:
            pnr: PNR containing special characters

        Returns:
            pnr: PNR with special characters removed
        """
        return re.sub('[\-\s\.\(\)]+', '', pnr)

    def _detect_serial_pnr(self):
        """
        Detects generic serial/pnr codes from self.text conforming to formats defined by regex pattern.

        Returns:
            A tuple of two lists with first list containing the detected pnr codeses and second list containing
            their corresponding substrings in the given text.

            For example:
                (['4sgx3e'], ['4sgx3e'])
        """
        # print 'detection for default task'
        pnr_list = []
        original_list = []
        pnr_list, original_list = self._detect_serial_key(pnr_list, original_list)
        self._update_processed_text(original_list)
        return pnr_list, original_list

    def _detect_serial_key(self, pnr_list=None, original_list=None):
        """
        Detects generic serial/pnr codes from self.text conforming to formats defined by regex pattern.

        This function is called by _detect_railway_pnr()

        Args:
            pnr_list: Optional, list to store detected pnr codeses
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            pnr codeses

        Returns:
            A tuple of two lists with first list containing the detected pnr codeses and second list containing
            their corresponding substrings in the given text.

            For example:
                (['4sgx3e'], ['4sgx3e'])
        """
        if pnr_list is None:
            pnr_list = []
        if original_list is None:
            original_list = []

        pnr = None
        pattern = re.compile(r'\s(([0-9]+[a-zA-Z]|[a-zA-Z]+[0-9])[A-Za-z0-9]*)\s').search(self.processed_text.lower())
        pattern2 = re.compile(r'\se([0-9]{4,20})\s').search(self.processed_text.lower())
        pattern3 = re.compile(r'\s([A-Z]{4,20})\s').search(self.processed_text.lower())
        pattern4 = re.compile(r'\s([A-Za-z0-9]*[^AaEeIiOoUu\+\-,!@#\$\^&\*\(\);/\|<>\s]{4,10}[A-Za-z0-9]+)[\s\.]') \
            .search(self.processed_text.lower())
        if pattern and len(pattern.group(1)) > 3:
            pnr = pattern.group(1)
        elif pattern2:
            pnr = pattern2.group(1)
        elif pattern3:
            pnr = pattern3.group(1)
        elif pattern4:
            pnr = pattern4.group(1)

        if pnr:
            pnr_list.append(pnr)
            original_list.append(pnr)

        return pnr_list, original_list

    def _update_processed_text(self, original_pnr_strings):
        """
        Replaces detected pnr codes with tag generated from entity_name used to initialize the object with

        A final string with all pnr codes replaced will be stored in object's tagged_text attribute
        A string with all pnr codes removed will be stored in object's processed_text attribute

        Args:
            original_pnr_strings: list of substrings of original text to be replaced with tag created from entity_name
        """
        for detected_text in original_pnr_strings:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')
