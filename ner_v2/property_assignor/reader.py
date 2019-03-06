from __future__ import absolute_import

import operator

import numpy as np
import pandas as pd
import regex as re  # We are using regex because it provides accurate word boundaries than built in re module

import ner_v2.detectors.utils as v2_utils
from ner_v2.property_assignor.fields import PropertyContextPatterns
from ner_v2.property_assignor.utils import clean_text


class PropertyDataField:
    """
    Just a namespace for columns in the data file. Not meant to be initialized. This could have been an Enum,
    but this provides a cleaner design than .value everywhere
    """
    property = "property"  # str
    prefixes = "prefixes"  # List[str]
    suffixes = "suffixes"  # List[str]
    bot_message_contexts = "bot_message_contexts"  # List[str]
    prefix_suffix_both_required = "prefix_suffix_both_required"  # bool


class PropertiesDataReader:
    @staticmethod
    def make_pattern(variants):
        # type: (List[Text]) -> Optional[Text]
        """
        Form either or regex pattern from variants by
        performing re.escape each member in variant, sorting them descending by length
        and joining them by "|". Whitespace only members will be dropped

        >>> make_pattern(variants=["a", "def", "bc"])
        u"(?:def|bc|a)"

        >>> make_pattern(variants=["a", "bc", "def"])
        ur"(?:def|bc|a)"

        Args:
            variants (list of str/Text): list of variants

        Returns:
            Text or None: raw Text pattern that can be passed to re.compile.
                If variants are only whitespace or variants is an empty list, None will be returned

        """
        variants = [clean_text(text=variant, drop_puncts=True, except_puncts=(u"_",)) for variant in variants]
        variants = [re.escape(variant) for variant in variants if variant]
        if not variants:
            return None

        variants = sorted(variants, key=lambda variant: len(variant), reverse=True)
        variants_pattern = u"(?:{})".format(u"|".join(variants))

        return variants_pattern

    @staticmethod
    def is_nan(value):
        # type: (Any) -> bool
        """
        Check if value is float and np.nan

        Args:
            value: value to check

        Returns:
            bool: True if value is np.nan

        """
        return isinstance(value, float) and np.isnan(value)

    @staticmethod
    def from_csv(csv_file_path, multi_field_delimiter=u"|", include_only=None):
        # type: (str, Text, Optional[Iterable[str]]) -> List[PropertyContextPatterns]
        """
        Read the csv file and return a dict mapping property to a tuple containing prefix, suffix,
        bot message regex patterns, etc
        See `PropertyContextPatterns` for all fields

        Note: The returned list is stable-sorted where properties which need both prefix and suffix to match appear
        first

        Args:
            csv_file_path (str): path to the csv file to read data from
            multi_field_delimiter (Text, optional): Separator to split data in cells of csv that are
                supposed to contain list of values. Defaults to u"|"
            include_only (list of str/Text, optional): List of properties to include in the returned dict.
                All other read property data will be ignored. Defaults to None which returns all properties data

        Returns:
            list: list containing namedtuples of type PropertyContextPatterns

        """
        if include_only is not None:
            include_only = set(include_only)

        df = pd.read_csv(csv_file_path, encoding="utf-8")
        df.dropna(subset=[PropertyDataField.property], inplace=True)

        data = []
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

            prefixes_pattern, suffixes_pattern, bot_contexts_pattern = None, None, None

            if not PropertiesDataReader.is_nan(prefixes):
                prefix_variants = v2_utils.ensure_str(prefixes).split(multi_field_delimiter)
                prefixes_pattern = PropertiesDataReader.make_pattern(variants=prefix_variants)

            if not PropertiesDataReader.is_nan(suffixes):
                suffix_variants = v2_utils.ensure_str(suffixes).split(multi_field_delimiter)
                suffixes_pattern = PropertiesDataReader.make_pattern(variants=suffix_variants)

            if not PropertiesDataReader.is_nan(bot_contexts):
                bot_contexs_variants = v2_utils.ensure_str(bot_contexts).split(multi_field_delimiter)
                bot_contexts_pattern = PropertiesDataReader.make_pattern(variants=bot_contexs_variants)

            if prefix_suffix_both_required and (prefixes_pattern is None or suffixes_pattern is None):
                raise ValueError(u"prefix_suffix_both_required is True but one of prefixes_pattern"
                                 u" and suffixes_pattern is null or just whitespace - {}".format(row))

            if all(pattern is None for pattern in [prefixes_pattern, suffixes_pattern, bot_contexts_pattern]):
                raise ValueError(u"All three - prefixes, suffixes, bot_contexts cannot be empty"
                                 u"or whitespace only. Row {}".format(row))

            data.append(
                PropertyContextPatterns(
                    property=property_,
                    prefixes_pattern=prefixes_pattern,
                    suffixes_pattern=suffixes_pattern,
                    bot_contexts_pattern=bot_contexts_pattern,
                    prefix_suffix_both_required=prefix_suffix_both_required
                )
            )

            # We want both required ones to be checked first. If there are multiple such items, then
            # the ordering is decided by the order they appear in the file, since .sort is stable
            data.sort(key=operator.attrgetter('prefix_suffix_both_required'), reverse=True)

        return data
