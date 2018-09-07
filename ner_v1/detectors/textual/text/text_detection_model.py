from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.constant import ENTITY_VALUE_DICT_KEY, ES_VERIFIED


class TextModelDetector(TextDetector):

    def detect_entity(self, text, **kwargs):
        self._process_text()
        values, original_texts = self._text_detection_with_variants()

        text_entity_verified_values = TextModelDetector.add_verification_source(values=values,
                                                                                verification_source_dict=
                                                                                {ES_VERIFIED: True})
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
            verification_source_dict = {"es_verified": True}

            >> add_verification_source(values, verification_source_dict)
                [{'es_verified': True, 'value': u'Chennai'},
                 {'es_verified': True, 'value': u'New Delhi'},
                 {'es_verified': True, 'value': u'chennai'}]
        """
        text_entity_verified_values = []
        for text_entity_value in values:
            text_entity_dict = {ENTITY_VALUE_DICT_KEY: text_entity_value}
            for verification_source_key in list(verification_source_dict.keys()):
                text_entity_dict[verification_source_key] = verification_source_dict[verification_source_key]
            text_entity_verified_values.append(text_entity_dict)
        return text_entity_verified_values
