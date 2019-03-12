from __future__ import absolute_import

import regex as re  # We are using regex because it provides accurate word boundaries than built in re module

import ner_v2.detectors.utils as v2_utils
from ner_v2.property_assignor.fields import AssignedProperty
from ner_v2.property_assignor.reader import PropertiesDataReader
from ner_v2.property_assignor.utils import clean_text


class PropertyAssignor(object):
    """
    This module assigns arbitrary properties to already detected entities. Say for example, once you have
    detected cities, you might want to assign some roles such as "arrival", "departure", "via"
    etc. based on thier contexts.

    This module takes in
        - text
        - spans that are substrings of the text that were detected as some entity
        - data file that contains context data for each property, such as what should appear before and after entity
          mention, what should appear in the bot message (it if is given) for this property to be assigned

    Attributes:
        _property_context_patterns (list): list containing PropertyContextPatterns items.
    """

    def __init__(self, properties_data_path, subset=None):
        # type: (str, List[str]) -> None
        """
        Args:
            properties_data_path (str): path to the csv file containing the properties data
            subset (list of str, optional): list of properties to assign from. Defaults to None, in that case all
                properties read from the data file are considered to be assigned from.
        """
        self._property_context_patterns = PropertiesDataReader.from_csv(  # type: List[PropertyContextPatterns]
            csv_file_path=properties_data_path,
            include_only=subset
        )

    def assign_properties(self, text, detected_spans, bot_message=None):
        # type: (Text, List[Text], Optional[Text]) -> List[AssignedProperty]
        """
        Assign properties to `detected_spans` based on their contexts

        Rough pseudocode:
            - Replace all detected spans in text with an entity placeholder
            - Drop punctuations, Reduce whitespace from text and bot_message
            - If `detected_spans` has only one item, matches are allowed throughout the text instead
                of being immediately around the detected entity. If there are more than one `detected_spans`
                then any prefix must strictly end just before the entity mention and any suffix must strictly start
                just after the entity mention
            - prop_from_bot = get the first property for which one of the bot contexts is present in bot message
            - For each replaced entity placeholder
                prefix = part of text before this entity placeholder
                suffix = part of text after this entity placeholder
                For each property
                    If both prefix and suffix must match
                        If both matches are found
                            Assign this property
                    Else if prefix is matched
                        Assign this property
                    Else if suffix is matched
                        Assign this property

                    If property is assigned
                        Break

                If no property was assigned and prop_from_bot is not null:
                    Assign prop_from_bot

        Known Limitations:
            - if any punctuations are expected in prefix or suffix like say for date range, 25th-26th, the "-" is
              prefix to "26th", will not work because we drop punctuations. However, with small
              modifications it is possible to get this working

        Args:
            text (str): the text from which entities were detetced
            detected_spans (list of str): list of substrings of text that were detected as some entity
            bot_message (str, optional): message from the bot in the last turn in the dialogue.
                Defaults to None

        Returns:
            list: list of AssignedProperty (namedtuple) of same length as `detected_spans`.
                Each AssignedProperty has two members
                    `property` which can be None or str - the property assigned to ith span and
                    `reason` which can be None or str - why was this property assign. Can be one of
                        "prefix_suffix" - both prefix and suffix patterns matched
                        "prefix" - Only prefix pattern matched
                        "suffix" - Only suffix pattern matched
                        "bot_message" - No prefix or suffix matched but bot message had terms to assign this property
                    `match_text` which can be None or str - part of text or bot_message due to which this property
                        was assigned. If `reason` is "prefix_suffix", matched prefix part and suffix part will be
                        joined by "|||"

        """
        entity_placeholder = u"__entity__"
        assigned_properties = [AssignedProperty(property=None, reason=None, match_text=None)
                               for _ in detected_spans]

        detected_spans = [(v2_utils.ensure_str(span), i) for i, span in enumerate(detected_spans)]
        detected_spans = sorted(detected_spans, key=lambda span_i: len(span_i[0]), reverse=True)

        for (span, i) in detected_spans:
            text = text.replace(span, entity_placeholder + str(i) + u"_", 1)

        text = clean_text(text, drop_puncts=True)
        if bot_message:
            bot_message = clean_text(bot_message, drop_puncts=True)

        strict_match = bool(len(detected_spans) > 1)

        for context_patterns in self._property_context_patterns:
            context_patterns.compile_patterns(strict_match=strict_match)

        property_from_bot_message = None
        if bot_message:
            for context_patterns in self._property_context_patterns:
                _, _, bot_message_match = context_patterns.get_matches(prefix=None,
                                                                       suffix=None,
                                                                       bot_message=bot_message)
                if bot_message_match:
                    property_from_bot_message = AssignedProperty(
                        property=context_patterns.property,
                        reason="bot_message",
                        match_text=bot_message_match
                    )
                    break

        for match in re.finditer(entity_placeholder + r"\d+_", text):
            start, end = match.span()
            detected_spans_index = int(text[start:end].rstrip(u"_").split(entity_placeholder)[-1])
            prefix = text[:start].strip()
            suffix = text[end + 1:].strip()

            for context_patterns in self._property_context_patterns:
                prefix_match, suffix_match, _ = context_patterns.get_matches(prefix=prefix,
                                                                             suffix=suffix,
                                                                             bot_message=None)
                if context_patterns.prefix_suffix_both_required:
                    if prefix_match and suffix_match:
                        assigned_properties[detected_spans_index] = AssignedProperty(
                            property=context_patterns.property,
                            reason="prefix_suffix",
                            match_text=prefix_match + u"|||" + suffix_match
                        )
                        break
                else:
                    if prefix_match:
                        assigned_properties[detected_spans_index] = AssignedProperty(
                            property=context_patterns.property,
                            reason="prefix",
                            match_text=prefix_match
                        )
                        break
                    elif suffix_match:
                        assigned_properties[detected_spans_index] = AssignedProperty(
                            property=context_patterns.property,
                            reason="suffix",
                            match_text=suffix_match
                        )
                        break

            if not assigned_properties[detected_spans_index].property and property_from_bot_message:
                assigned_properties[detected_spans_index] = property_from_bot_message

        return assigned_properties
