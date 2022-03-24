"""
Important note: bad regexes that cause catastrophic backtracking can hang your Python processes (especially because
Python's re does not release the GIL! If you are putting this module behind a web server be wary of ReDoS attacks.
Unfortunately there is no clean way around that, so make sure to set processing killing timeouts like harakiri for
uwsgi
"""

from __future__ import absolute_import

from typing import List

from chatbot_ner.config import ner_logger
from lib.nlp.text_normalization import perform_asr_correction

try:
    import regex as re

    _re_flags = re.UNICODE | re.V1 | re.WORD
    _regex_available = True

except ImportError:
    ner_logger.warning('Error importing `regex` lib, falling back to stdlib re')
    import re

    _re_flags = re.UNICODE
    _regex_available = False


class RegexDetector(object):
    MATCH_PLACEHOLDER = '▁▁'
    DEFAULT_FLAGS = _re_flags
    """
    Detect entity from text using a regular expression pattern.
    Note: Module will not return any empty or whitespace only matches

    Attributes:
         entity_name (str) : holds the entity name
         text (str) : holds the original text
         tagged_text (str) : holds the detected entities replaced by self.tag
         processed_text (str) : holds the text left to be processed
         matches (list of _sre.SRE_Match): re.finditer match objects
         pattern (raw str or str or unicode): pattern to be compiled into a re object
    """

    def __init__(self, entity_name, pattern, asr_enabled=False, re_flags=DEFAULT_FLAGS, max_matches=50):
        """
        Args:
            entity_name (str): an indicator value as tag to replace detected values
            pattern (raw str or str or unicode): pattern to be compiled into a re object
            asr_enabled (bool) : True if message is from ASR and needs to be processed accordingly
            re_flags (int): flags to pass to re.compile.
                Defaults to `regex.U | regex.V1 | regex.WORD`  for `regex` lib  and `re.U` for stdlib `re`
            max_matches (int): maximum number of matches to consider.

        Raises:
            TypeError: if the given pattern fails to compile
        """
        self.entity_name = entity_name
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.asr_enabled = asr_enabled
        self.uncompiled_pattern = pattern
        try:
            self.pattern = re.compile(pattern, flags=re_flags)
        except re.error:
            # In very rare cases it is possible we encounter a pattern that is invalid for V1 engine but works just
            # fine on V0 engine/Python's built in re. E.g. nested character sets '[[]]'
            if _regex_available and (re_flags & re.V1):
                re_flags = (re_flags ^ re.V1) | re.V0
                self.pattern = re.compile(pattern, flags=re_flags)
                ner_logger.warning(f'Failed to compile `{pattern}` with regex.V1, falling back to regex.V0')
            else:
                raise
        self.max_matches = max_matches
        self.tag = '__' + self.entity_name + '__'

    def detect_entity(self, text):
        """
        Run regex pattern on the provided text and return non overlapping group 0 matches

        Args:
            text (str): Text to find patterns on

        Returns:
            tuple containing
                list: list containing substrings of text that matched the set pattern
                list: list containing corresponding substrings of original text that were identified as entity values

        Note:
            In this case both returned lists are identical.

        Example:
            >> regex_detector = RegexDetector(entity_name='numerals', pattern='\\d+')
            >> regex_detector.detect_entity('My phone is 911234567890. Call me at 2pm')
            (['911234567890', '2'], ['911234567890', '2'])
            >> regex_detector.tagged_text
            'My phone is __numerals__. Call me at __numerals__pm'

        """
        self.text = text
        if self.asr_enabled:
            self.processed_text = perform_asr_correction(self.text, self.uncompiled_pattern)
        else:
            self.processed_text = self.text
        self.tagged_text = self.text
        match_list, original_list = self._detect_regex()
        self._update_processed_text(match_list)
        return match_list, original_list

    def _detect_regex(self):
        """
        Detects text based on the aforementioned regex

        Returns:
            tuple containing
                list: list containing substrings of text that matched the set pattern
                list: list containing corresponding substrings of original text that were identified as entity values
        """
        original_list = []  # type: List[str]
        match_list = []  # type: List[str]
        for match in self.pattern.finditer(self.processed_text):
            if match.group(0).strip():
                match_text = match.group(0)
                match_list.append(match_text)
                original_list.append(match_text)
            if len(match_list) >= self.max_matches:
                break
        return match_list, original_list

    def _update_processed_text(self, match_list):
        # type: (List[str]) -> None
        """
        Update processed text by removing already found entity values and update tagged text to replace found
        values with the set tag

        Args:
            match_list: list containing substrings of text that matched the set pattern
        """
        for detected_text in match_list:
            self.tagged_text = self.tagged_text.replace(detected_text, RegexDetector.MATCH_PLACEHOLDER, 1)
            self.processed_text = self.processed_text.replace(detected_text, '', 1)
        self.tagged_text = self.tagged_text.replace(RegexDetector.MATCH_PLACEHOLDER, self.tag)
