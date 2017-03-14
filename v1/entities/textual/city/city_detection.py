from v1.entities.textual.text.text_detection import TextDetection


class CityDetector(object):

    def __init__(self, entity_name):
        self.entity_name = entity_name
        self.text = ''
        self.text_dict = {}
        self.tagged_text = ''
        self.processed_text = ''
        self.city = []
        self.original_city_text = []
        self.text_detection_object = TextDetection(entity_name=entity_name)
        self.hs_city = None
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
        """
        Take text and returns location details
        :param text:
        :return: tuple (list of location , original text)
        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text


        city_data = self.detect_city()
        self.city = city_data[0]
        self.original_city_text = city_data[1]
        return city_data

    def detect_city_format(self, city_list=[], original_list=[]):
        """
        Detects city if it is present in the chat
        :param city_list:
        :param original_list:
        :return:
        """
        city_list_from_text_entity, original_list = self.text_detection_object.detect_entity(self.text)
        self.tagged_text = self.text_detection_object.tagged_text
        self.processed_text = self.text_detection_object.processed_text
        for city in city_list_from_text_entity:
            city_list.append(city)

        return city_list, original_list

    def update_processed_text(self, original_list):
        """
        This function updates text by replacing already detected entity
        :return:
        """
        for detected_text in original_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')

    def set_hs_city(self, city):
        self.hs_city = city

