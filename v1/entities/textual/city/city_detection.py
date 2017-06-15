from models.constants import CITY_ENTITY_TYPE, CITY_VALUE
from models.crf.read_model import PredictCRF
from v1.constant import MODEL_VERIFIED, MODEL_NOT_VERIFIED
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

    def detect_entity(self, text, run_model=True):
        """Detects city in the text string

        Args:
            text: string to extract entities from
            run_model: Boolean True if model needs to run else False
        Returns:
            A tuple of two lists with first list containing the detected city and second list containing their
            corresponding substrings in the given text.

            For example:

                (['Mumbai'], ['bombay'])

            Additionally this function assigns these lists to self.city and self.original_city_text attributes
            respectively.

        """
        self.text = ' ' + text + ' '
        self.text = self.text.lower()
        self.processed_text = self.text.lower()
        self.tagged_text = self.text.lower()
        city_data = []
        if run_model:
            city_data = self.city_model_detection()
        if not run_model or not city_data[0]:
            city_data = self.detect_city()
            city_data = city_data + ([],)
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
        This function calls get_model_output() method of PredictCRF class and verifies the values returned by it.


        If the cities provided by crf are present in the datastore, it sets the value MODEL_VERIFIED
        else MODEL_NOT_VERFIED is set.

        And returns the final list of all detected items with each value containing a field to show whether the value if verified or 
        not

        For Example:
            Note*:  before calling this method you need to call set_bot_message() to set a bot message.

            
            self.bot_message = 'Please help me with your departure city?'
            self.text = 'mummbai'

            final values of all lists:
                model_output = [{'city':'mummbai', 'from': 1, 'to': 0, 'via': 0}]

                The for loop verifies each city in model_output list by checking whether it exists in datastore or not(by running elastic search).
                If not then sets the value MODEL_NOT_VERIFIED else MODEL_VERIFIED

                finally it returns ['Mumbai'], ['mummbai'], [MODEL_VERIFIED]

        For Example:
        
            self.bot_message = 'Please help me with your departure city?'
            self.text = 'dehradun'

            final values of all lists:
                model_output = [{'city':'dehradun', 'from': 1, 'to': 0, 'via': 0}]

                Note*: Dehradun is not present in out datastore so it will take original value as entity value.

                finally it returns ['dehradun'], ['dehradun'], [MODEL_NOT_VERIFIED]

        """
        predict_crf = PredictCRF()
        model_output = predict_crf.get_model_output(entity_type=CITY_ENTITY_TYPE, bot_message=self.bot_message,
                                                    user_message=self.text)
        city_list, original_list, model_detection_type = [], [], []
        for city_dict in model_output:
            city_list_from_text_entity, original_list_from_text_entity = \
                self.text_detection_object.detect_entity(city_dict[CITY_VALUE])
            if city_list_from_text_entity:
                city_list.extend(city_list_from_text_entity)
                original_list.extend(original_list_from_text_entity)
                model_detection_type.append(MODEL_VERIFIED)
            else:
                city_list.append(city_dict[CITY_VALUE])
                original_list.append(city_dict[CITY_VALUE])
                model_detection_type.append(MODEL_NOT_VERIFIED)
        self.update_processed_text(original_list)

        return city_list, original_list, model_detection_type

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
