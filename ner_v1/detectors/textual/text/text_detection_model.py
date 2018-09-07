from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.constant import ENTITY_VALUE_DICT_KEY, DATASTORE_VERIFIED


class TextModelDetector(TextDetector):
    """
    This class is inherited from the TextDetector class.
    This class is primarily used to detect text type entities and additionally return the detection source for the same.
    """
    def detect_entity(self, text, **kwargs):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of detected text entities  and their corresponding original substrings in text respectively.
        The first list being a list of dicts with the verification source and the values.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched successfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.

        Args:
            text (unicode): string to extract textual entities from
            **kwargs: it can be used to send specific arguments in future. for example, fuzziness, previous context.
        Returns:
            tuple:
                list: containing list of dicts with the source of detection for the entity value and
                entity value as defined into datastore
                list: containing corresponding original substrings in text

        Example:
            DataStore().get_entity_dictionary('city')

                Output:
                    {
                        u'Agartala': [u'', u'Agartala'],
                        u'Barnala': [u'', u'Barnala'],
                        ...
                        u'chennai': [u'', u'chennai', u'tamilnadu', u'madras'],
                        u'hyderabad': [u'hyderabad'],
                        u'koramangala': [u'koramangala']
                    }

            text_detection = TextModelDetector('city')
            text_detection.detect_entity('Come to Chennai, TamilNadu,  I will visit Delhi next year')

                Output:
                    ([{'datastore_verified': True, 'value': u'Chennai'},
                      {'datastore_verified': True, 'value': u'New Delhi'},
                      {'datastore_verified': True, 'value': u'chennai'}]
                    , ['chennai', 'delhi', 'tamilnadu'])

            text_detection.tagged_text

                Output:
                    ' come to __city__, __city__,  i will visit __city__ next year '

        Additionally this function assigns these lists to self.text_entity_values and self.original_texts attributes
        respectively.
        """
        self._process_text(text)
        values, original_texts = self._text_detection_with_variants()

        text_entity_verified_values = TextModelDetector.add_verification_source(values=values,
                                                                                verification_source_dict=
                                                                                {DATASTORE_VERIFIED: True})
        self.text_entity_values, self.original_texts = text_entity_verified_values, original_texts

        return self.text_entity_values, self.original_texts

    @staticmethod
    def add_verification_source(values, verification_source_dict):
        """
        Add the verification source for the detected entities
        Args:
            values (list): List of detected text type entities
            verification_source_dict (dict): Dict consisting of the verification source and value.
        Returns:
            text_entity_verified_values (list): List of dicts consisting of the key and values for the keys
            value and verification source
        Example:
            values = [u'Chennai', u'New Delhi', u'chennai']
            verification_source_dict = {"datastore_verified": True}

            >> add_verification_source(values, verification_source_dict)
                [{'datastore_verified': True, 'value': u'Chennai'},
                 {'datastore_verified': True, 'value': u'New Delhi'},
                 {'datastore_verified': True, 'value': u'chennai'}]
        """
        text_entity_verified_values = []
        for text_entity_value in values:
            text_entity_dict = {ENTITY_VALUE_DICT_KEY: text_entity_value}
            for verification_source_key in list(verification_source_dict.keys()):
                text_entity_dict[verification_source_key] = verification_source_dict[verification_source_key]
            text_entity_verified_values.append(text_entity_dict)
        return text_entity_verified_values
