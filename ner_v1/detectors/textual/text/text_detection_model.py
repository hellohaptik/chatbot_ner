import re
from ner_v1.detectors.textual.text.text_detection import TextDetector
from ner_v1.constant import ENTITY_VALUE_DICT_KEY, DATASTORE_VERIFIED, CRF_MODEL_VERIFIED
from models.crf_v2.crf_detect_entity import CrfDetection


class TextModelDetector(TextDetector):
    """
    This class is inherited from the TextDetector class.
    This class is primarily used to detect text type entities using the datastore as well as the the CRF
    model if trained.
    """
    def __init__(self, entity_name, source_language_script, cloud_storage=False, cloud_embeddings=False,
                 live_crf_model_path=None):
        super(TextModelDetector, self).__init__(entity_name=entity_name, source_language_script=source_language_script)
        self.cloud_storage = cloud_storage
        self.cloud_embeddings = cloud_embeddings
        self.live_crf_model_path = live_crf_model_path

    def detect_entity(self, text, **kwargs):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of detected text entities  and their corresponding original substrings in text respectively.
        The first list being a list of dicts with the verification source and the values.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched successfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.
        In addition to this method also runs the CRF MODEL if trained and provides the results for the given entity.
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
                    ([{'datastore_verified': True,'crf_model_verified': True, 'value': u'Chennai'},
                      {'datastore_verified': True,'crf_model_verified': False, 'value': u'New Delhi'},
                      {'datastore_verified': False,'crf_model_verified': True, 'value': u'chennai'}]
                    , ['chennai', 'delhi', 'tamilnadu'])

            text_detection.tagged_text

                Output:
                    ' come to __city__, __city__,  i will visit __city__ next year '

        Additionally this function assigns these lists to self.text_entity_values and self.original_texts attributes
        respectively.
        """
        crf_original_texts = []
        if self.live_crf_model_path:
            crf_model = CrfDetection(entity_name=self.entity_name, cloud_storage=self.cloud_storage,
                                     cloud_embeddings=self.cloud_embeddings,
                                     live_crf_model_path=self.live_crf_model_path)

            crf_original_texts = crf_model.detect_entity(text=text)

        values, original_texts = super(TextModelDetector, self).detect_entity(text, **kwargs)

        text_entity_verified_values, original_texts = self.combine_results(values=values, original_texts=original_texts,
                                                                           crf_original_texts=crf_original_texts)
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

    def combine_results(self, values, original_texts, crf_original_texts):
        """
        This method is used to combine the results provided by the datastore search and the
        crf_model if trained.
        Args:
            values (list): List of values detected by datastore
            original_texts (list): List of original texts present in the texts for which value shave been
                                   detected
            crf_original_texts (list): Entities detected by the Crf Model
        Returns:
            combined_values (list): List of dicts each dict consisting of the entity value and additionally
                                    the keys for the datastore and crf model detection
            combined_original_texts (list): List of original texts detected by the datastore and the crf model.
        """
        unprocessed_crf_original_texts = []

        combined_values = self._add_verification_source(values=values,
                                                        verification_source_dict=
                                                        {DATASTORE_VERIFIED: True,
                                                         CRF_MODEL_VERIFIED: False}
                                                        )
        combined_original_texts = original_texts
        for i in range(len(crf_original_texts)):
            match = False
            for j in range(len(original_texts)):
                if crf_original_texts[i] == original_texts[j]:
                    combined_values[j][CRF_MODEL_VERIFIED] = True
                    match = True
                elif re.findall(r'\b%s\b' % crf_original_texts[i], original_texts[j]):
                    match = True
            if not match:
                unprocessed_crf_original_texts.append(crf_original_texts[i])

        unprocessed_crf_original_texts_verified = self._add_verification_source(values=unprocessed_crf_original_texts,
                                                                                verification_source_dict=
                                                                                {DATASTORE_VERIFIED: False,
                                                                                 CRF_MODEL_VERIFIED: True}
                                                                                )
        combined_values.extend(unprocessed_crf_original_texts_verified)
        combined_original_texts.extend(unprocessed_crf_original_texts)

        return combined_values, combined_original_texts
