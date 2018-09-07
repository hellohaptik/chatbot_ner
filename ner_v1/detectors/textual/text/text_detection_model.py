from ner_v1.detectors.textual.text.text_detection import TextDetector


class TextModelDetector(TextDetector):

    def detect_entity(self, text, **kwargs):
        self._process_text()
        values, original_texts = self._text_detection_with_variants()

        self.text_entity_values, self.original_texts = values, original_texts

        return self.text_entity_values, self.original_texts
