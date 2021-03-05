from __future__ import absolute_import
import re
from six.moves import range

def get_number_from_number_word(text, number_word_dict):
    """
    Detect numbers from numerals text
    Args:
        text (str): text to detect number from number words
        number_word_dict (dict): dict containing scale and increment of each number word
    Returns:
        detected_number_list (list): list of numeric value detected from text
        detected_original_text_list (list): list of original text for numeric value detected
    Examples:
        [In]  >>  number_word_dict = {'one': NumberVariant(scale=1, increment=1),
                                      'two': NumberVariant(scale=1, increment=2),
                                      'three': NumberVariant(scale=1, increment=3),
                                      'thousand': NumberVariant(scale=1000, increment=0),
                                      'four': NumberVariant(scale=1, increment=4),
                                      'hundred': NumberVariant(scale=100, increment=0)
                                      }
        [In]  >>  _get_number_from_numerals('one thousand two',  number_word_dict)
        [Out] >> (['1002'], ['one thousand two'])
        [In]  >> _get_number_from_numerals('one two three',  number_word_dict)
        [Out] >> (['1', '2', '3'], ['one', 'two', 'three'])
        [In]  >> _get_number_from_numerals('two hundred three four hundred three',  number_word_dict)
        [Out] >> (['103', '403'], ['one hundred three', 'four hundred three'])
    """
    # FIXME: conversion from float -> int is lossy, consider using Decimal class
    detected_number_list = []
    detected_original_text_list = []

    # exclude single char scales word from word number map dict
    number_word_dict = {word: number_map for word, number_map in number_word_dict.items()
                        if (len(word) > 1 and number_map.increment == 0) or number_map.scale == 1}
    text = text.strip()
    if not text:
        return detected_number_list, detected_original_text_list

    whitespace_pattern = re.compile(r'(\s+)', re.UNICODE)
    parts = []
    _parts = whitespace_pattern.split(u' ' + text)
    for i in range(2, len(_parts), 2):
        parts.append(_parts[i - 1] + _parts[i])

    current = result = 0
    current_text, result_text = '', ''
    on_number = False
    prev_digit_len = 0

    for part in parts:
        word = part.strip()

        if word not in number_word_dict:
            if on_number:
                result_text += current_text
                original = result_text.strip()
                number_detected = result + current
                if float(number_detected).is_integer():
                    number_detected = int(number_detected)
                detected_number_list.append(number_detected)
                detected_original_text_list.append(original)

            result = current = 0
            result_text, current_text = '', ''
            on_number = False
        else:
            scale, increment = number_word_dict[word].scale, number_word_dict[word].increment
            digit_len = max(len(str(int(increment))), len(str(scale)))

            if digit_len == prev_digit_len:
                if on_number:
                    result_text += current_text
                    original = result_text.strip()
                    number_detected = result + current
                    if float(number_detected).is_integer():
                        number_detected = int(number_detected)
                    detected_number_list.append(number_detected)
                    detected_original_text_list.append(original)

                result = current = 0
                result_text, current_text = '', ''

            # handle where only scale is mentioned without unit, for ex - thousand(for 1000), hundred(for 100)
            current = 1 if (scale > 1 and current == 0 and increment == 0) else current
            current = current * scale + increment
            current_text += part
            if scale > 1:
                result += current
                result_text += current_text
                current = 0
                current_text = ''
            on_number = True
            prev_digit_len = digit_len

    if on_number:
        result_text += current_text
        original = result_text.strip()
        number_detected = result + current
        if float(number_detected).is_integer():
            number_detected = int(number_detected)
        detected_number_list.append(number_detected)
        detected_original_text_list.append(original)

    return detected_number_list, detected_original_text_list


def get_list_from_pipe_sep_string(text_string):
    """
    Split numerals
    Args:
        text_string (str):  text
    Returns:
        (list) : list containing numeral after split
    """
    text_list = text_string.split("|")
    return [x.lower().strip() for x in text_list if x.strip()]
