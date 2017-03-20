import re

from v1.entities.textual.text.text_detection import TextDetector


class CityAdvanceDetector(object):
    def __init__(self, entity_name):
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.city = []
        self.original_date_text = []
        self.form_check = True
        self.entity_name = entity_name
        self.text_detection_object = TextDetector(entity_name=entity_name)
        self.outbound_message = None
        self.tag = '__' + entity_name + '__'

    def detect_entity(self, text, form_check=False):
        """
        Take text and returns city details
        :param text:
        :param form:
        :return: tuple (list of city , original text)
        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        self.form_check = form_check
        city_data = self.detect_city()
        self.city = city_data[0]
        self.original_city_text = city_data[1]
        return city_data

    def detect_city(self):
        """
        Takes in a message string and returns a list of dictionary containing departure and arrival city along with the original text
        :return: tuple (list of city , original text)
        """
        # print 'detection for default task'
        city_list = []
        original_list = []
        city_list, original_list = self.detect_departure_arrival_city_prepositions(city_list, original_list)
        self.update_processed_text(original_list)
        city_list, original_list = self.detect_departure_arrival_city(city_list, original_list)
        self.update_processed_text(original_list)
        city_list, original_list = self.detect_arrival_departure_city(city_list, original_list)
        self.update_processed_text(original_list)
        city_list, original_list = self.detect_departure_city(city_list, original_list)
        self.update_processed_text(original_list)
        city_list, original_list = self.detect_arrival_city(city_list, original_list)
        self.update_processed_text(original_list)
        city_list, original_list = self.detect_any_city(city_list, original_list)
        self.update_processed_text(original_list)

        return city_list, original_list

    def detect_departure_arrival_city(self, city_list, original_list):
        """
        Detects departure and arrival city
        :param city_list:
        :param original_list:
        :return:
        """

        patterns = re.findall(r'\s(([A-Za-z]+)\s*(\-|to|2|and)\s*([A-Za-z]+))\.?\b', self.processed_text.lower())

        for pattern in patterns:
            original = None
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            original = pattern[0]
            departure_city = self.__get_city_name(pattern[1])
            arrival_city = self.__get_city_name(pattern[3])

            if departure_city and arrival_city:
                city['departure_city'] = departure_city
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def detect_departure_arrival_city_prepositions(self, city_list, original_list):
        """
        Identifies cities if prepositions are present
        :param city_list:
        :param original_list:
        :return:
        """
        patterns = re.findall(
            r'\s((?:from|frm|departing|depart|leaving|leave)\s*([A-Za-z]+)\s*(?:and|to|2|for|fr|arriving|arrive|reaching|reach|rch)\s*([A-Za-z]+))\.?\b',
            self.processed_text.lower())

        for pattern in patterns:
            original = None
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            original = pattern[0]
            departure_city = self.__get_city_name(pattern[1])
            arrival_city = self.__get_city_name(pattern[2])

            if departure_city and arrival_city:
                city['departure_city'] = departure_city
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def detect_arrival_departure_city(self, city_list, original_list):
        """
        Detects arrival and departure city
        :param city_list:
        :param original_list:
        :return:
        """

        patterns = re.findall(
            r'\s((?:and|to|2|for|fr|arriving|arrive|reaching|reach|rch)\s*([A-Za-z]+)\s*(?:from|frm|departing|depart|leaving|leave)\s*([A-Za-z]+))\.?\b',
            self.processed_text.lower())

        for pattern in patterns:
            original = None
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            original = pattern[0]
            departure_city = self.__get_city_name(pattern[2])
            arrival_city = self.__get_city_name(pattern[1])

            if departure_city and arrival_city:
                city['departure_city'] = departure_city
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def detect_departure_city(self, city_list, original_list):
        """
        Detects departure city
        :param city_list:
        :param original_list:
        :return:
        """

        patterns = re.findall(
            r'\s((from|frm|departing|depart|leaving|leave|origin city\:|departure city\:)\s*([A-Za-z]+))\.?\s',
            self.processed_text.lower())

        for pattern in patterns:
            original = None
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            departure_city = self.__get_city_name(pattern[2])

            if departure_city:
                original = pattern[0]
                city['departure_city'] = departure_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def detect_arrival_city(self, city_list, original_list):
        """
        detects arrival city
        :param city_list:
        :param original_list:
        :return:
        """
        patterns = re.findall(
            r'\s((to|2|for|fr|arriving|arrive|reaching|reach|rch|destination city\:|arrival city\:)\s*([A-Za-z]+))\.?\s',
            self.processed_text.lower())

        for pattern in patterns:
            original = None
            pattern = list(pattern)
            city = {
                'departure_city': None,
                'arrival_city': None
            }
            arrival_city = self.__get_city_name(pattern[2])

            if arrival_city:
                original = pattern[0]
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def detect_any_city(self, city_list, original_list):
        """
        detects city based on the outbound message
        :param city_list:
        :param original_list:
        :return:
        """
        departure_city_flag = False
        arrival_city_flag = False
        if self.outbound_message:
            departure_regexp = re.compile(
                r'departure city|origin city|origin|traveling from|leaving from|flying from|travelling from')
            arrival_regexp = re.compile(
                r'traveling to|travelling to|arrival city|arrival|destination city|destination|leaving to|flying to')
            if departure_regexp.search(self.outbound_message) is not None:
                departure_city_flag = True
            elif arrival_regexp.search(self.outbound_message) is not None:
                arrival_city_flag = True

        patterns = re.findall(r'\s((.+))\.?\b', self.processed_text.lower())

        for pattern in patterns:
            original = None
            pattern = list(pattern)
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            city_selected, original_selected = self.__get_city_name_list(pattern[1])
            if city_selected:

                original = original_selected[0]
                if len(city_selected) > 1:
                    city['departure_city'] = city_selected[0]
                    city['arrival_city'] = city_selected[-1]
                else:
                    if departure_city_flag and not arrival_city_flag:
                        city['departure_city'] = city_selected[0]
                        city['arrival_city'] = None
                    elif not departure_city_flag and arrival_city_flag:
                        city['departure_city'] = None
                        city['arrival_city'] = city_selected[0]
                    else:
                        city['departure_city'] = city_selected[0]
                        city['arrival_city'] = None

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def __get_city_name(self, text):
        """
        Gets the city name
        :param text:
        :return:
        """

        city_list, original_list = self.text_detection_object.detect_entity(text)
        if city_list:
            return city_list[0]
        else:
            return None

    def __get_city_name_list(self, text):
        """
        Gets the city name
        :param text:
        :return:
        """

        city_list, original_list = self.text_detection_object.detect_entity(text)
        if city_list:
            return city_list, original_list
        else:
            return None, None

    def update_processed_text(self, original_city_strings):
        """
        This function updates text by replacing already detected city
        :return:
        """
        for detected_text in original_city_strings:
            if detected_text:
                self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
                self.processed_text = self.processed_text.replace(detected_text, '')

    def set_outbound_message(self, outbound_message):
        self.outbound_message = outbound_message
