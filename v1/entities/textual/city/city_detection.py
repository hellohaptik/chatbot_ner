from models.constants import CITY_ENTITY_TYPE, CITY_VALUE
from models.crf.read_model import PredictCRF
from v1.entities.constant import flag_model_run
from v1.entities.textual.text.text_detection import TextDetector


class CityDetector(object):
    """
    CityDetector detects city from the text it similar to TextDetection and inherits TextDetection to perform its
    operation.


    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected city entities would be replaced with on calling detect_entity()
        text_dict: dictionary to store lemmas, stems, ngrams used during detection process
        tagged_text: string with city entities replaced with tag defined by entity_name
        text_entity: list to store detected entities from the text
        original_city_entity: list of substrings of the text detected as entities
        processed_text: string with detected time entities removed
        tag: entity_name prepended and appended with '__'
    """

    def __init__(self, entity_name):
        """
        Initializes a CityDetector object with given entity_name

        Args:
            entity_name: A string by which the detected substrings that correspond to text entities would be replaced
                         with on calling detect_entity()
        """

        self.entity_name = entity_name
        self.text = ''
        self.bot_message = ''
        self.text_dict = {}
        self.tagged_text = ''
        self.processed_text = ''
        self.city = []
        self.original_city_text = []
        self.text_detection_object = TextDetector(entity_name=entity_name)
        self.tag = '__' + self.entity_name + '__'

    def detect_city(self):
        """
        Takes a message and writtens the list of city present in the text
        :return: tuple (list of location , original text)
        """
        city_list = []
        original_list = []
        city_list, original_list = self.detect_city_format(city_list, original_list)
        self.update_processed_text(original_list)
        return city_list, original_list

    def detect_entity(self, text):
        """Detects city in the text string

        Args:
            text: string to extract entities from

        Returns:
            A tuple of two lists with first list containing the detected city and second list containing their
            corresponding substrings in the given text.

            For example:

                (['Mumbai'], ['bombay'])

            Additionally this function assigns these lists to self.city and self.original_city_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text.lower()
        self.tagged_text = self.text.lower()
        if flag_model_run:
            city_data = self.city_model_detection()
        else:
            city_data = self.detect_city()
        self.city = city_data[0]
        self.original_city_text = city_data[1]
        return city_data

    def detect_city_format(self, city_list=[], original_list=[]):
        """
        Detects city from self.text conforming to formats defined by regex pattern.



        Args:
            city_list: Optional, list to store detected cities
            original_list: Optional, list to store corresponding substrings of given text which were detected as
                            cities

        Returns:
            A tuple of two lists with first list containing the detected cities and second list containing their
            corresponding substrings in the given text. For example:

            For example:

                (['Mumbai'], ['bombay'])
        """
        city_list_from_text_entity, original_list = self.text_detection_object.detect_entity(self.text)
        self.tagged_text = self.text_detection_object.tagged_text
        self.processed_text = self.text_detection_object.processed_text
        for city in city_list_from_text_entity:
            city_list.append(city)

        return city_list, original_list

    def city_model_detection(self):
        """

        :return:
        """
        predict_crf = PredictCRF()
        model_output = predict_crf.get_model_output(entity_type=CITY_ENTITY_TYPE, bot_message=self.bot_message,
                                                    user_message=self.text)
        city_list, original_list = [], []
        for city_dict in model_output:
            city_list_from_text_entity, original_list_from_text_entity = \
                self.text_detection_object.detect_entity(city_dict[CITY_VALUE])
            if city_list_from_text_entity:
                city_list.extend(city_list_from_text_entity)
                original_list.extend(original_list_from_text_entity)
            else:
                city_list.extend(city_dict[CITY_VALUE])
                original_list.extend(city_dict[CITY_VALUE])

        return city_list, original_list

    def update_processed_text(self, original_list):
        """
        Replaces detected cities with tag generated from entity_name used to initialize the object with

        A final string with all cities replaced will be stored in object's tagged_text attribute
        A string with all cities removed will be stored in object's processed_text attribute

        Args:
            original_city_strings: list of substrings of original text to be replaced with tag created from entity_name
        """
        for detected_text in original_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: string
        """

        self.bot_message = bot_message
