from __future__ import absolute_import

import string

import regex as re  # We are using regex because it provides accurate word boundaries than built in re module
import six

import ner_v2.detectors.utils as v2_utils

__punctuations = set(string.punctuation)
__whitespace_pattern = re.compile(r"\s+", flags=re.UNICODE)


def replace_puncts(text, replace_with=u" ", except_puncts=(u"_",)):
    # type: (Text, Text, Tuple[Text]) -> Text
    """
    Replace all punctuations (string.punctuation) except those in `except_puncts` with `replace_with`

    Args:
        text (str): Text to replace punctuations in
        replace_with (str, optional): string to replace punctuations with. Defaults to a single space
        except_puncts (tuple of str, optional): tuple containing punctuations to ignore.
            Defaults to tuple with single member - underscore

    Returns:
        str: text with all punctuations (string.punctuation) except those in `except_puncts` replaced
            with `replace_with`
    """
    puncts = __punctuations.copy() - set(except_puncts)
    puncts_pattern = u"[{}]+".format(re.escape(u"".join(puncts)))
    puncts_pattern = re.compile(puncts_pattern, flags=re.UNICODE)
    return puncts_pattern.sub(replace_with, text)


def clean_text(text, drop_puncts=True, except_puncts=(u"_",)):
    # type: (Text, bool, Tuple[Text]) -> Text
    """
    Decode text and replace punctuations if `ignore_puncts` is True. If text is not string type
    it is returned as is.

    Args:
        text (str): text to clean up
        drop_puncts (bool, optional): whether to replace punctuations with a space. Defaults to True
        except_puncts (tuple of str, optional): tuple containing punctuations to ignore.
            Defaults to tuple with single member - underscore

    Returns:
        str: if text is non empty string, a decoded string with optionally punctuations replaced.
            Otherwise the text is returned as is.
    """
    if text and isinstance(text, six.string_types):
        text = v2_utils.ensure_str(text)
        if drop_puncts:
            text = replace_puncts(text=text, replace_with=u" ", except_puncts=except_puncts)
            text = __whitespace_pattern.sub(u" ", text).strip()
    return text
