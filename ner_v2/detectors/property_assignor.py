import collections
import string

import numpy as np
import pandas as pd
import regex as re  # We are using regex because it provides accurate word boundaries than built in re module
import six

import ner_v2.detectors.utils as v2_utils
from lib.nlp.const import whitespace_tokenizer

__punctuations = set(string.punctuation)

AssignedProperty = collections.namedtuple("AssignedProperty", ["property", "reason"])

PropertyContextPatterns = collections.namedtuple("PropertyContextPatterns", [
    "prefixes_pattern",  # Optional[regex.Regex] - pattern for the prefix
    "suffixes_pattern",  # Optional[regex.Regex] - pattern for the suffix
    "bot_contexts_pattern",  # Optional[regex.Regex] - pattern for the bot message
    "prefix_within_n_words",  # int - How many words behind the entity to look for prefix in
    "suffix_within_n_words",  # int - How many words ahead the entity to look for prefix in
    "prefix_suffix_both_required"  # bool - If both prefix and suffix must match to assign this property
])


class PropertyDataField:
    property = "property"  # str
    prefixes = "prefixes"  # List[str]
    suffixes = "suffixes"  # List[str]
    bot_message_contexts = "bot_message_contexts"  # List[str]
    prefix_within_n_words = "prefix_within_n_words"  # int
    suffix_within_n_words = "suffix_within_n_words"  # int
    prefix_suffix_both_required = "prefix_suffix_both_required"  # bool


def replace_puncts(text, replace_with=u" ", except_puncts=(u"_",)):
    # type: (Union[unicode, str], unicode, Tuple[Union[unicode, str]]) -> Union[unicode, str]
    """
    Replace all punctuations (string.punctuation) except those in `except_puncts` with `replace_with`

    Args:
        text (str/unicode): Text to replace punctuations in
        replace_with (str/unicode, optional): string to replace punctuations with. Defaults to a single space
        except_puncts (tuple of unicode/str, optional): tuple containing punctuations to ignore.
            Defaults to tuple with single member - underscore

    Returns:
        str/unicode: text with all punctuations (string.punctuation) except those in `except_puncts` replaced
            with `replace_with`

    """
    puncts = __punctuations.copy() - set(except_puncts)
    puncts_pattern = u"[{}]+".format(re.escape(u"".join(puncts)))
    return re.sub(puncts_pattern, replace_with, text, flags=re.UNICODE)


class PropertiesDataReader:

    @staticmethod
    def make_pattern(variants, add_word_boundaries=True):
        # type: (List[Union[unicode, str]], bool) -> Optional[unicode]
        """
        Form either or regex pattern from variants by
        performing re.escape each member in variant, sorting them descending by length
        and joining them by "|". Whitespace only members will be dropped

        >>> make_pattern(variants=["a", "def", "bc"], add_word_boundaries=False)
        u"(?:def|bc|a)"

        >>> make_pattern(variants=["a", "bc", "def"], add_word_boundaries=True)
        ur"\b(?:def|bc|a)\b"

        Args:
            variants (list of str/unicode): list of variants
            add_word_boundaries (bool, optional): Add regex word boundaries (\b) to the pattern. Defaults to True

        Returns:
            unicode or None: raw unicode pattern that can be passed to re.compile.
                If variants are only whitespace or variants is an empty list, None will be returned

        """
        variants = [v2_utils.ensure_str(variant).strip() for variant in variants]
        variants = [re.escape(variant) for variant in variants if variant]
        if not variants:
            return None

        variants = sorted(variants, key=lambda variant: len(variant), reverse=True)
        variants_pattern = u"(?:{})".format(u"|".join(variants))
        if add_word_boundaries:
            variants_pattern = r"\b" + variants_pattern + r"\b"
        return variants_pattern

    @staticmethod
    def is_nan(value):
        return isinstance(value, float) and np.isnan(value)

    @staticmethod
    def from_csv(csv_file_path, multi_field_delimiter=u"|", include_only=None):
        # type: (str, unicode, Optional[Iterable[str]]) -> collections.OrderedDict[unicode, PropertyContextPatterns]
        """
        Read the csv file and return a dict mapping property to a tuple containing prefix, suffix,
        bot message regex patterns, number of words to search around the entity mention, etc
        See `PropertyContextPatterns` for all fields

        Args:
            csv_file_path (str): path to the csv file to read data from
            multi_field_delimiter (unicode, optional): Separator to split data in cells of csv that are
                supposed to contain list of values. Defaults to u"|"
            include_only (list of str/unicode, optional): List of properties to include in the returned dict.
                All other read property data will be ignored. Defaults to None which returns all properties data

        Returns:
            collections.OrderedDict: dict mapping str to PropertyContextPatterns

        """
        if include_only is not None:
            include_only = set(include_only)

        df = pd.read_csv(csv_file_path, encoding="utf-8")
        df.drop_duplicates(subset=[PropertyDataField.property], inplace=True)
        df.dropna(subset=[PropertyDataField.property], inplace=True)
        data = collections.OrderedDict()
        for _, row in df.iterrows():
            property_ = row[PropertyDataField.property]

            if include_only and property_ not in include_only:
                continue

            prefixes = row[PropertyDataField.prefixes]
            suffixes = row[PropertyDataField.suffixes]
            bot_contexts = row[PropertyDataField.bot_message_contexts]
            prefix_suffix_both_required = row[PropertyDataField.prefix_suffix_both_required]

            if not isinstance(prefix_suffix_both_required, bool):
                raise ValueError("Column prefix_suffix_both_required must be of type bool - either true or false")

            prefix_within_n_words = max(0, int(row[PropertyDataField.prefix_within_n_words]))
            suffix_within_n_words = max(0, int(row[PropertyDataField.suffix_within_n_words]))

            prefixes_pattern, suffixes_pattern, bot_contexts_pattern = None, None, None

            if not PropertiesDataReader.is_nan(prefixes):
                prefix_variants = v2_utils.ensure_str(prefixes).split(multi_field_delimiter)
                prefixes_pattern = PropertiesDataReader.make_pattern(variants=prefix_variants,
                                                                     add_word_boundaries=True)
                if prefixes_pattern:
                    prefixes_pattern = re.compile(prefixes_pattern, flags=re.UNICODE | re.V1 | re.WORD)

            if not PropertiesDataReader.is_nan(suffixes):
                suffix_variants = v2_utils.ensure_str(suffixes).split(multi_field_delimiter)
                suffixes_pattern = PropertiesDataReader.make_pattern(variants=suffix_variants,
                                                                     add_word_boundaries=True)
                if suffixes_pattern:
                    suffixes_pattern = re.compile(suffixes_pattern, flags=re.UNICODE | re.V1 | re.WORD)

            if not PropertiesDataReader.is_nan(bot_contexts):
                bot_contexs_variants = v2_utils.ensure_str(bot_contexts).split(multi_field_delimiter)
                bot_contexts_pattern = PropertiesDataReader.make_pattern(variants=bot_contexs_variants,
                                                                         add_word_boundaries=True)
                if bot_contexts_pattern:
                    bot_contexts_pattern = re.compile(bot_contexts_pattern, flags=re.UNICODE | re.V1 | re.WORD)

            if prefix_suffix_both_required and (prefixes_pattern is None or suffixes_pattern is None):
                raise ValueError(u"{} - prefix_suffix_both_required is True but one of prefixes_pattern"
                                 u" and suffixes_pattern is null or just whitespace".format(row))

            if all(pattern is None for pattern in [prefixes_pattern, suffixes_pattern, bot_contexts_pattern]):
                raise ValueError(u"{} - All three - prefixes, suffixes, bot_contexts cannot be empty"
                                 u"or whitespace only".format(row))

            data[property_] = PropertyContextPatterns(prefixes_pattern=prefixes_pattern,
                                                      suffixes_pattern=suffixes_pattern,
                                                      bot_contexts_pattern=bot_contexts_pattern,
                                                      prefix_within_n_words=prefix_within_n_words,
                                                      suffix_within_n_words=suffix_within_n_words,
                                                      prefix_suffix_both_required=prefix_suffix_both_required)

        return data


class PropertyAssignor(object):
    """
    This module assigns arbitrary properties to already detected entities. Say for example, once you detected cities,
    you might want to assign some roles such as "arrival", "departure", "via" etc. based on thier contexts.
    This module takes in
        - text
        - spans that are substrings of the text that were detected as some entity
        - data file that contains context data for each property, such as what should appear before and after entity
          mention, what should appear in the bot message (it if is given) for this property to be assigned

    It allows for configurable look ahead and look behind. Each property can ask for it"s prefixes and suffixes be
    searched in previous N or next M tokens around the entity mention respectively


    Attributes:
        _property_context_patterns (dict): dict mapping str to PropertyContextPatterns.
            Maps each property to prefix, suffix, bot message patterns, look ahead length, look behind length, etc
    """

    def __init__(self, properties_data_path, subset=None):
        # type: (str, List[str]) -> None
        """
        Args:
            properties_data_path (str): path to the csv file containing the properties data
            subset (list of str, optional): list of properties to assign from. Defaults to None, in that case all
                properties read from the data file are considered to be assigned from.
        """
        self._property_context_patterns = PropertiesDataReader.from_csv(csv_file_path=properties_data_path,
                                                                        include_only=subset)

    def _clean_text(self, text, ignore_puncts):
        # type: (Union[str, unicode, Any], bool) -> Union[unicode, Any]
        """
        Decode text and replace punctuations if `ignore_puncts` is True. If text is not string type
        it is returned as is.

        Args:
            text (str/unicode): text to clean up
            ignore_puncts (bool): whether to drop punctuations from the text and replace them with a space

        Returns:
            unicode or Any: if text is non empty string, a decoded string with optionally punctuations replaced.
                Otherwise the text is returned as is.
        """
        if text and isinstance(text, six.string_types):
            text = v2_utils.ensure_str(text)
            if ignore_puncts:
                text = replace_puncts(text=text, replace_with=u" ", except_puncts=(u"_",))
        return text

    def assign_properties(self, text, detected_spans, bot_message=None, ignore_puncts=True):
        # type: (unicode, List[unicode], Optional[unicode], bool) -> List[AssignedProperty]
        """
        Assign properties to `detected_spans` based on their contexts

        Rough pseudocode:
            - First drop punctuations from text and bot_message if ignore_puncts is True
            - Split both by whitespace and join them back by single space
            - Replace all detected spans in text with an entity placeholder
            - For each replaced entity placeholder
                For each property
                    Match prefix within N words before this entity
                    Match suffix within M words after this entity
                    If both prefix and suffix must match
                        If both matches are found
                            Assign this property
                    Else if prefix is matched
                        Assign this property
                    Else if suffix is matched
                        Assign this property
                    Else if bot message is given and has required terms
                        Assign this property

                    If property is assigned
                        Break

        Args:
            text (str/unicode): the text from which entities were detetced
            detected_spans (list of str/unicode): list of substrings of text that were detected as some entity
            bot_message (str/unicode, optional): message from the bot in the last turn in the dialogue.
                Defaults to None
            ignore_puncts (bool, optional): whether to drop punctuations from the text and bot message
                and replace them with a space. Defaults to True

        Returns:
            list: list of AssignedProperty (namedtuple) of same length as `detected_spans`.
                Each AssignedProperty has two members 
                    `property` which can be None or str - the property assigned to ith span and
                    `reason` which can be None or str - why was this property assign. Can be one of 
                        "prefix_suffix" - both prefix and suffix patterns matched
                        "prefix" - Only prefix pattern matched
                        "suffix" - Only suffix pattern matched
                        "bot_message" - No prefix or suffix matched but bot message had terms to assign this property

        """
        # TODO: Write unit tests
        # TODO: Reduce complexity of this function if possible
        entity_placeholder = u"__entity__"
        assigned_properties = [AssignedProperty(property=None, reason=None) for _ in detected_spans]

        text = self._clean_text(text, ignore_puncts=ignore_puncts)
        bot_message = self._clean_text(bot_message, ignore_puncts=ignore_puncts)

        detected_spans = [(v2_utils.ensure_str(span), i) for i, span in enumerate(detected_spans)]
        detected_spans = sorted(detected_spans, key=lambda span_i: len(span_i[0]), reverse=True)

        for (span, i) in detected_spans:
            text = text.replace(span, entity_placeholder + str(i) + u"_", 1)

        text_tokens = whitespace_tokenizer.tokenize(text)
        if bot_message:
            bot_message = u" ".join(whitespace_tokenizer.tokenize(bot_message))

        for token_ind, token in enumerate(text_tokens):

            if not token.startswith(entity_placeholder):
                continue

            assigned_property, reason = None, None
            detected_spans_ind = int(token.rstrip(u"_").split(entity_placeholder)[-1])

            for property_, context_patterns in six.iteritems(self._property_context_patterns):

                prefix = u" ".join(text_tokens[max(0, token_ind - context_patterns.prefix_within_n_words): token_ind])
                suffix = u" ".join(text_tokens[token_ind + 1: token_ind + 1 + context_patterns.suffix_within_n_words])

                prefix_found = (prefix and
                                context_patterns.prefixes_pattern and
                                context_patterns.prefixes_pattern.search(prefix))

                suffix_found = (suffix and
                                context_patterns.suffixes_pattern and
                                context_patterns.suffixes_pattern.search(suffix))

                if context_patterns.prefix_suffix_both_required:
                    if prefix_found and suffix_found:
                        assigned_property, reason = property_, "prefix_suffix"
                elif prefix_found:
                    assigned_property, reason = property_, "prefix"
                elif suffix_found:
                    assigned_property, reason = property_, "suffix"

                if (not assigned_property and
                        bot_message and
                        context_patterns.bot_contexts_pattern and
                        context_patterns.bot_contexts_pattern.search(bot_message)):
                    assigned_property, reason = property_, "bot_message"

                if assigned_property:
                    assigned_properties[detected_spans_ind] = AssignedProperty(property=assigned_property,
                                                                               reason=reason)
                    break

        return assigned_properties
