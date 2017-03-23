import re

from v1.entities.textual.text.text_detection import TextDetector


class CityAdvanceDetector(object):
    """
    Detects city subject to conditions like "arrival_city" and "departure_city". These cities are returned in a
    dictionary with keys 'arrival_city' and 'departure_city'. This class uses TextDetector to detect the city values.

    This class can be used to detect cities specific to scenarios involving a departure and arrival city for example in
    travel related text

    Attributes:
        text: string to extract entities from
        entity_name: string by which the detected date entities would be replaced with on calling detect_entity()
        tagged_text: string with date entities replaced with tag defined by entity name
        processed_text: string with detected date entities removed
        date: list of date entities detected
        original_city_text: list to store substrings of the text detected as city entities
        tag: entity_name prepended and appended with '__'
        text_detector_object: TextDetector object used to detect dates in the given text
        bot_message: boolean, set as the outgoing bot text/message
    """

    def __init__(self, entity_name):
        """
        Initializes the CityAdvanceDetector object with given entity_name

        Args:
            entity_name: A string by which the detected date entity substrings would be replaced with on calling
                        detect_entity()
        """

        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.city = []
        self.original_city_text = []
        self.form_check = True
        self.entity_name = entity_name
        self.text_detection_object = TextDetector(entity_name=entity_name)
        self.bot_message = None
        self.tag = '__' + entity_name + '__'

    def detect_entity(self, text, form_check=False):
        """
        Detects all city strings in text and returns two lists of detected city entities and their corresponding
        original substrings in text respectively.

        Args:
            text: string to extract city entities from

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'arrival_city'
            and 'departure_city' keys and dictionaries returned form TextDetector as their values,
            for each detected city, and second list containing corresponding original substrings in text

        Examples:

        Additionally this function assigns these lists to self.city and self.original_city_text attributes
        respectively.

        """
        self.text = ' ' + text + ' '
        self.processed_text = self.text
        self.tagged_text = self.text
        self.form_check = form_check
        city_data = self._detect_city()
        self.city = city_data[0]
        self.original_city_text = city_data[1]
        return city_data

    def _detect_city(self):
        """
        Detects "departure" and "arrival" from the object's text attribute

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'departure_city'
            and 'arrival_city' keys and dictionaries returned form TextDetector as their values,
            for each detected date, and second list containing corresponding original substrings in text

        """
        # print 'detection for default task'
        city_list = []
        original_list = []
        city_list, original_list = self._detect_departure_arrival_city_prepositions(city_list, original_list)
        self._update_processed_text(original_list)
        city_list, original_list = self._detect_departure_arrival_city(city_list, original_list)
        self._update_processed_text(original_list)
        city_list, original_list = self._detect_arrival_departure_city(city_list, original_list)
        self._update_processed_text(original_list)
        city_list, original_list = self._detect_departure_city(city_list, original_list)
        self._update_processed_text(original_list)
        city_list, original_list = self._detect_arrival_city(city_list, original_list)
        self._update_processed_text(original_list)
        city_list, original_list = self._detect_any_city(city_list, original_list)
        self._update_processed_text(original_list)

        return city_list, original_list

    def _detect_departure_arrival_city(self, city_list, original_list):
        """
        Finds <any text><space(s)><'-' or 'to' or '2'><space(s)><any text> in the given text.
        It  splits the text into two parts on '-' or 'to' or '2'
        and detects the departure city in the first (left) part and detects arrival city in the second (right) part

        Args:
            city_list: Optional, list to store dictionaries of detected cities
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure and arrival type city entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'departure_city'
            and 'arrival_city' keys and dictionaries returned form TextDetector as their values,
            for each detected city, and second list containing corresponding original substrings in text
        """

        patterns = re.findall(r'\s(([A-Za-z]+)\s*(\-|to|2|and)\s*([A-Za-z]+))\.?\b', self.processed_text.lower())

        for pattern in patterns:
            original = None
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            original = pattern[0]
            departure_city = self._get_city_name(pattern[1])
            arrival_city = self._get_city_name(pattern[3])

            if departure_city and arrival_city:
                city['departure_city'] = departure_city
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def _detect_departure_arrival_city_prepositions(self, city_list, original_list):
        """
        Finds <preposition><any text><space(s)><'-' or 'to' or '2' or preposition><space(s)><any text> in the given
        text.
        It  splits the text into two parts on '-' or 'to' or '2'
        and detects the departure city in the first (left) part and detects arrival city in the second (right) part

        Args:
            city_list: Optional, list to store dictionaries of detected cities
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure and arrival type city entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'departure_city'
            and 'arrival_city' keys and dictionaries returned form TextDetector as their values,
            for each detected city, and second list containing corresponding original substrings in text
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
            departure_city = self._get_city_name(pattern[1])
            arrival_city = self._get_city_name(pattern[2])

            if departure_city and arrival_city:
                city['departure_city'] = departure_city
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def _detect_arrival_departure_city(self, city_list, original_list):
        """
        Finds <preposition><any text><space(s)><'-' or 'to' or '2' or preposition><space(s)><any text> in the given
        text.
        It  splits the text into two parts on '-' or 'to' or '2'
        and detects the arrival city in the first (left) part and detects departure city in the second (right) part

        Args:
            city_list: Optional, list to store dictionaries of detected cities
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure and arrival type city entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'departure_city'
            and 'arrival_city' keys and dictionaries returned form TextDetector as their values,
            for each detected city, and second list containing corresponding original substrings in text
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
            departure_city = self._get_city_name(pattern[2])
            arrival_city = self._get_city_name(pattern[1])

            if departure_city and arrival_city:
                city['departure_city'] = departure_city
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def _detect_departure_city(self, city_list, original_list):
        """
        Finds departure type cities in the given text by matching few keywords like 'from', 'departing',
        'leaving', 'departure city', 'departing', 'going to' . It detects dates in the part of text right to these
        keywords.

        Args:
            city_list: Optional, list to store dictionaries of detected cities
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure and arrival type city entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'departure_city'
            and 'arrival_city' keys and dictionaries returned form TextDetector as their values,
            for each detected city, and second list containing corresponding original substrings in text
        """
        patterns = re.findall(
            r'\s((from|frm|departing|depart|leaving|leave|origin city\:|departure city\:|going to)\s*([A-Za-z]+))\.?\s',
            self.processed_text.lower())

        for pattern in patterns:
            original = None
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            departure_city = self._get_city_name(pattern[2])

            if departure_city:
                original = pattern[0]
                city['departure_city'] = departure_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def _detect_arrival_city(self, city_list, original_list):
        """
        Finds return type dates in the given text by matching few keywords like 'arriving', 'arrive',
        'reaching', 'reach', 'destination city:' . It detects city in the part of text right
        to these keywords.

        Args:
            city_list: Optional, list to store dictionaries of detected cities
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure and arrival type city entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'departure_city'
            and 'arrival_city' keys and dictionaries returned form TextDetector as their values,
            for each detected city, and second list containing corresponding original substrings in text
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
            arrival_city = self._get_city_name(pattern[2])

            if arrival_city:
                original = pattern[0]
                city['arrival_city'] = arrival_city

                city_list.append(city)
                original_list.append(original)

        return city_list, original_list

    def _detect_any_city(self, city_list, original_list):
        """
        This function makes use of bot_message. In a chatbot user might just enter city name based on the
        previous question asked by the bot. So, if the previous question asked by the bot contains words like 
        departure city, origin city, origin and if the current message contains city then we assign the 
        detected city as departure_city. if the previous message contains words like arrival city, destination city,
        flying to in the bots message and the current message contains the city then we assign the detected city as 
        arrival city
    

        Args:
            city_list: Optional, list to store dictionaries of detected cities
            original_list: Optional, list to store corresponding original substrings of text which were detected as
                            departure and arrival type city entities

        Returns:
            Tuple containing two lists, first containing dictionaries, each containing 'departure_city'
            and 'arrival_city' keys and dictionaries returned form TextDetector as their values,
            for each detected city, and second list containing corresponding original substrings in text
        """
        departure_city_flag = False
        arrival_city_flag = False
        if self.bot_message:
            departure_regexp = re.compile(
                r'departure city|origin city|origin|traveling from|leaving from|flying from|travelling from')
            arrival_regexp = re.compile(
                r'traveling to|travelling to|arrival city|arrival|destination city|destination|leaving to|flying to')
            if departure_regexp.search(self.bot_message) is not None:
                departure_city_flag = True
            elif arrival_regexp.search(self.bot_message) is not None:
                arrival_city_flag = True

        patterns = re.findall(r'\s((.+))\.?\b', self.processed_text.lower())

        for pattern in patterns:
            original = None
            pattern = list(pattern)
            city = {
                'departure_city': None,
                'arrival_city': None
            }

            city_selected, original_selected = self._get_city_name_list(pattern[1])
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

    def _get_city_name(self, text):
        """Returns the city name by calling TextDetection object

        Args:
            text: text on which detection needs to run

        Return:
            Name of the city

        """

        city_list, original_list = self.text_detection_object.detect_entity(text)
        if city_list:
            return city_list[0]
        else:
            return None

    def _get_city_name_list(self, text):
        """Returns the list of cities by calling TextDetection object

        Args:
            text: text on which detection needs to run

        Return:
            list of cities along with the original text
        """

        city_list, original_list = self.text_detection_object.detect_entity(text)
        if city_list:
            return city_list, original_list
        else:
            return None, None

    def _update_processed_text(self, original_city_strings):
        """
        Replaces detected date entities with tag generated from entity_name used to initialize the object with

        A final string with all date entities replaced will be stored in object's tagged_text attribute
        A string with all date entities removed will be stored in object's processed_text attribute

        Args:
            original_city_strings: list of substrings of original text to be replaced with tag created from entity_name
        """

        for detected_text in original_city_strings:
            if detected_text:
                self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
                self.processed_text = self.processed_text.replace(detected_text, '')

    def set_bot_message(self, bot_message):
        """
        Sets the object's bot_message attribute

        Args:
            bot_message: string
        """

        self.bot_message = bot_message
