from __future__ import absolute_import

import collections

import regex as re  # We are using regex because it provides accurate word boundaries than built in re module

AssignedProperty = collections.namedtuple("AssignedProperty", ["property", "reason", "match_text"])


class PropertyContextPatterns(object):
    """
    Data object encapsulating a property and regex patterns and other attrs.
    """
    def __init__(self, property,
                 prefixes_pattern,
                 suffixes_pattern,
                 bot_contexts_pattern,
                 prefix_suffix_both_required):
        # type: (Text, Optional[Text], Optional[Text], Optional[Text], bool) -> None
        """
        Args:
            property (str): name for the property
            prefixes_pattern (str, optional): regex pattern to search in prefix for this property
            suffixes_pattern (str, optional): regex pattern to search in suffix for this property
            bot_contexts_pattern (str, optional): regex pattern to search in bot message for this property
            prefix_suffix_both_required (str, optional): are both match in prefix and match in suffix required
        """
        self.property = property
        self.prefixes_pattern = prefixes_pattern
        self.suffixes_pattern = suffixes_pattern
        self.bot_contexts_pattern = bot_contexts_pattern
        self.prefix_suffix_both_required = prefix_suffix_both_required

        self._prefix_re = None
        self._suffix_re = None
        self._bot_contexts_re = None

    def compile_patterns(self, add_word_boundaries=True, strict_match=True):
        # type: (bool, bool) -> None
        """
        Compile regex patterns and optionally add word boundaries and terminal symbols

        Args:
            add_word_boundaries (bool, optional): Add regex word boundaries "\b" to the patterns. Defaults to True
            strict_match (bool, optional): if True, a end symbol "$" is added to prefix pattern which means the
                match should at the end of prefix; a start symbol "^" is added to suffix pattern which means the
                match should begin at the start of the suffix. Defaults to True

        Returns:
            None

        """
        if self.prefixes_pattern:
            prefix_pattern = self.prefixes_pattern
            if add_word_boundaries:
                prefix_pattern = r"\b" + prefix_pattern + r"\b"
            if strict_match:
                prefix_pattern = prefix_pattern + "$"
            self._prefix_re = re.compile(prefix_pattern, flags=re.UNICODE | re.WORD | re.V1)

        if self.suffixes_pattern:
            suffix_pattern = self.suffixes_pattern
            if add_word_boundaries:
                suffix_pattern = r"\b" + suffix_pattern + r"\b"
            if strict_match:
                suffix_pattern = "^" + suffix_pattern
            self._suffix_re = re.compile(suffix_pattern, flags=re.UNICODE | re.WORD | re.V1)

        if self.bot_contexts_pattern:
            bot_contexts_pattern = self.bot_contexts_pattern
            if add_word_boundaries:
                bot_contexts_pattern = r"\b" + bot_contexts_pattern + r"\b"
            self._bot_contexts_re = re.compile(bot_contexts_pattern, flags=re.UNICODE | re.WORD | re.V1)

    def get_matches(self, prefix=None, suffix=None, bot_message=None):
        # type: (Optional[Text], Optional[Text], Optional[Text])
        # -> Tuple[Optional[Text], Optional[Text], Optional[Text]]
        """
        Search given prefix, suffix and bot_message with compiled patterns and return matches if found

        Args:
            prefix (str, optional): prefix to the detected entity
            suffix (str, optional): suffix to the detected entity
            bot_message (str, optional): bot message in the last turn

        Returns:
            tuple: tuple containing three members
                None or str: part of the prefix that matched. None if nothing matched
                None or str: part of the suffix that matched. None if nothing matched
                None or str: part of the bot message that matched. None if nothing matched

        """
        def search(pattern, text):
            matched_text = None
            if pattern and text:
                match = pattern.search(text)
                if match is not None:
                    matched_text = match.group(0)
            return matched_text

        prefix_match = search(self._prefix_re, prefix)
        suffix_match = search(self._suffix_re, suffix)
        bot_message_match = search(self._bot_contexts_re, bot_message)
        return prefix_match, suffix_match, bot_message_match
