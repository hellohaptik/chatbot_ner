from __future__ import absolute_import
import re


class RegexReplace(object):
    """
    This class is used to perform regex operations
    Its a class which can be used to perform various regex operations like substitution, pattern matching, searching,
    etc.
    Currently, we have added functionality that will perform substitution over strings.

    For Example:
        pattern_list = [('[\,\?]', ''),(r'\bu\b','you')]
        regex = RegexReplace(pattern_list)
        output = regex.text_substitute('Hey, where are u going?')
        print output
        >> 'Hey where are you going'

    Attributes:
        pattern_list: List of tuples -> [(pattern_to_search, pattern_to_replace),...]
        pattern_compile: Object of 're' gets created for each pattern present in the list

    """

    def __init__(self, pattern_list):
        """Initializes a RegexReplace object

        Args:
            pattern_list: List of tuples -> [(pattern_to_search, pattern_to_replace),...]
        """

        self.pattern_list = pattern_list
        self.pattern_compile = [re.compile(pattern[0], re.IGNORECASE | re.UNICODE) for pattern in self.pattern_list]

    def text_substitute(self, text):
        """
        This function will substitute or replace the pattern with some other string from the text

        Args:
            text: text on which substitution needs to be performed

        Returns:
            str: text
            For example:
                pattern_list = [('[\,\?]', ''),(r'\bu\b','you')]
                regex = RegexReplace(pattern_list)
                output = regex.text_substitute('Hey, where are u going?')
                print output
                >> 'Hey where are you going'

        """
        processed_text = text
        for i, compiled_pattern in enumerate(self.pattern_compile):
            processed_text = compiled_pattern.sub(self.pattern_list[i][1], processed_text)
        return processed_text
