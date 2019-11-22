from language_utilities.constant import ENGLISH_LANG
from models.crf_v2.crf_detect_entity import CrfDetection
from ner_v1.detectors.textual.text.text_detection import TextDetector
import six


class TextModelDetector(TextDetector):
    """
    This class is inherited from the TextDetector class.
    This class is primarily used to detect text type entities using the datastore as well as the the CRF
    model if trained.
    """

    def __init__(self,
                 entity_name,
                 language=ENGLISH_LANG,
                 live_crf_model_path=None,
                 read_embeddings_from_remote_url=False,
                 read_model_from_s3=False,
                 **kwargs):
        """
        Args:
            entity_name (str): name of the entity. Same as the entity name under which data is indexed in DataStore
            language (str): ISO 639 code for the language to detect entities in
            live_crf_model_path (str): path to the crf model, either on disk or s3
            read_embeddings_from_remote_url (bool, optional): if True, read embeddings from remote url configured in
                                                              chatbot_ner.config. Defaults to False
            read_model_from_s3 (bool, optional): if True, use live_crf_model_path to read model from s3 instead
                                                 of local disk. Defaults to False
        """
        super(TextModelDetector, self).__init__(entity_name=entity_name,
                                                source_language_script=language,
                                                translation_enabled=False)
        self.read_model_from_s3 = read_model_from_s3
        self.read_embeddings_from_remote_url = read_embeddings_from_remote_url
        self.live_crf_model_path = live_crf_model_path

    def detect_entity(self, text, free_text_detection_results=None, **kwargs):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of detected text entities  and their corresponding original substrings in text respectively.
        The first list being a list of dicts with the verification source and the values.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched successfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.
        In addition to this method also runs the CRF MODEL if trained and provides the results for the given entity.
        Args:
            text (str or unicode): string to extract textual entities from
            free_text_detection_results(list of str): list of previous detected values
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
            crf_model = CrfDetection(entity_name=self.entity_name,
                                     read_model_from_s3=self.read_model_from_s3,
                                     read_embeddings_from_remote_url=self.read_embeddings_from_remote_url,
                                     live_crf_model_path=self.live_crf_model_path)

            crf_original_texts = crf_model.detect_entity(text=text)

        # Access free_text_detection_results(list of str).
        # If present replace crf_original_texts with free_text_detection_results.
        # Call combine results to .combine_results() from dictionary detection and free_text_detection_results.
        if free_text_detection_results is None:
            free_text_detection_results = []

        values, original_texts = super(TextModelDetector, self).detect_entity(
            text, free_text_detection_results=free_text_detection_results, **kwargs)

        text_entity_verified_values, original_texts = \
            self.combine_results(values=values,
                                 original_texts=original_texts,
                                 free_text_detection_results=free_text_detection_results)
        self.text_entity_values, self.original_texts = text_entity_verified_values, original_texts

        return self.text_entity_values, self.original_texts

    def detect_entity_bulk(self, texts, free_text_detection_results=None, **kwargs):
        """
        Detects all textual entities in text that are similar to variants of 'entity_name' stored in the datastore and
        returns two lists of list of detected text entities  and their corresponding original substrings
        for each sentence in text respectively.
        The first list being a list of list of dicts with the verification source and the values.
        Note that datastore stores number of values under a entity_name and each entity_value has its own list of
        variants, whenever a variant is matched successfully, the entity_value whose list the variant belongs to,
        is returned. For more information on how data is stored, see Datastore docs.
        In addition to this method also runs the CRF MODEL if trained and provides the results for the given entity.

        Args:
            texts (list of strings): natural language sentence(s) to extract entities from
            free_text_detection_results(list of lists of str): values from previous detection
            **kwargs: it can be used to send specific arguments in future. for example, fuzziness, previous context.

        Returns:
            tuple:
                list of lists(bulk detect): containing list of dicts with the source of detection
                for the entity value and entity value as defined into datastore

                list of lists(bulk detect): containing corresponding original substrings in text

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
                text_detection = TextDetector('city')
                list_of_sentences = ['Come to Chennai, TamilNadu,  I will visit Delhi next year',
                                    'I live in Delhi]

                text_detection.detect_entity(list_of_sentences)
                    Output:
                        (   [
                                [u'Chennai', u'New Delhi', u'chennai'],
                                [u'New Delhi']
                            ],
                            [
                                ['chennai', 'delhi', 'tamilnadu'],
                                [delhi]
                            ]
                        )

                text_detection.tagged_text
                    Output:
                        [
                            ' come to __city__, __city__,  i will visit __city__ next year ',
                            ' i live in __city__ '
                        ]

        Additionally this function assigns these lists to self.text_entity_values and self.original_texts attributes
        respectively.
        """

        crf_original_texts = []

        # Access free_text_detection_results(list of lists).
        # If present replace crf_original_texts with free_text_detection_results.
        # Call .combine_results() to combine results from dictionary detection and free_text_detection_results.
        if free_text_detection_results is None:
            free_text_detection_results = []

        values_list, original_texts_list = super(TextModelDetector, self).detect_entity_bulk(
            texts, free_text_detection_results=free_text_detection_results, **kwargs)
        text_entity_values_list, original_texts_detected_list = [], []

        for inner_free_text_detection_results, inner_values, inner_original_texts in six.moves.zip_longest(
                free_text_detection_results,
                values_list,
                original_texts_list):
            text_entity_verified_values, original_texts = \
                self.combine_results(
                    values=inner_values, original_texts=inner_original_texts,
                    free_text_detection_results=inner_free_text_detection_results if
                    inner_free_text_detection_results else [])
            text_entity_values_list.append(text_entity_verified_values)
            original_texts_detected_list.append(original_texts)
        return text_entity_values_list, original_texts_detected_list
