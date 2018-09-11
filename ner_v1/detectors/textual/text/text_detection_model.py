from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.constant import ENTITY_VALUE_DICT_KEY, DATASTORE_VERIFIED, CRF_MODEL_VERIFIED
from models.crf_v2.crf_detect_entity import CrfDetection


class TextModelDetector(TextDetector):
    """
    This class is inherited from the TextDetector class.
    This class is primarily used to detect text type entities and additionally return the detection source for the same.
    """
    def __init__(self, entity_name, source_language_script, cloud_storage=False, cloud_embeddings=False,
                 live_crf_model_path=''):
        super(TextModelDetector, self).__init__(entity_name=entity_name, source_language_script=source_language_script)
        self.cloud_storage = cloud_storage
        self.cloud_embeddings = cloud_embeddings
        self.live_crf_model_s3_path = live_crf_model_path

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
        values, original_texts = super(TextModelDetector, self).detect_entity(text, **kwargs)
        text_entity_verified_values = self._add_verification_source(values=values,
                                                                    verification_source_dict=
                                                                    {DATASTORE_VERIFIED: True})
        crf_model = CrfDetection(entity_name=self.entity_name, cloud_storage=self.cloud_storage,
                                 cloud_embeddings=self.cloud_embeddings,
                                 live_crf_model_path=self.live_crf_model_s3_path)
        crf_original_text = crf_model.detect_entity(text=text)

        crf_entity_verified_values = self._add_verification_source(values=crf_original_text,
                                                                   verification_source_dict=
                                                                   {CRF_MODEL_VERIFIED: True})
        text_entity_verified_values.extend(crf_entity_verified_values)
        original_texts.extend(crf_original_text)
        self.text_entity_values, self.original_texts = text_entity_verified_values, original_texts
        return self.text_entity_values, self.original_texts

    def _add_verification_source(self, values, verification_source_dict):
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
            text_entity_dict.update(verification_source_dict)
            text_entity_verified_values.append(text_entity_dict)
        return text_entity_verified_values
