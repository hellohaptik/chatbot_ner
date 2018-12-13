
def get_number_from_numerals(text, number_word_dict):
    """
    Detect numbers from numerals text
    Args:
        text (str): text to detect number from number words
        number_word_dict (collections.namedtuple('NumberVariant', ['scale', 'increment'])):
                    Named tuple containing scale and increment of each number word

    Returns:
        detected_number_list (list): list of numeric value detected from text
        detected_original_text_list (list): list of original text for numeric value detected

    Examples:
        [In]  >>  number_word_dict = {'one': (1, 1), 'two': (1, 2), 'three': (1, 3), 'thousand': (1000, 0),
                                      'four': (1, 4), 'hundred': (100, 0)
                                      }

        [In]  >>  _get_number_from_numerals('one thousand two',  number_word_dict)
        [Out] >> (['1002'], ['one thousand two'])

        [In]  >> _get_number_from_numerals('one two three',  number_word_dict)
        [Out] >> (['1', '2', '3'], ['one', 'two', 'three'])

        [In]  >> _get_number_from_numerals('two hundred three four hundred three',  number_word_dict)
        [Out] >> (['103', '403'], ['one hundred three', 'four hundred three'])

    """
    detected_number_list = []
    detected_original_text_list = []
    current = result = 0
    current_text, result_text = '', ''
    on_number = False
    prev_digit_len = 0
    for word in text.split():
        if word not in number_word_dict:
            if on_number:
                original = (result_text.strip() + " " + current_text.strip()).strip()
                number_detected = int(result + current) if float(result + current).is_integer() \
                    else result + current
                detected_number_list.append(number_detected)
                detected_original_text_list.append(original)

            result = current = 0
            result_text, current_text = '', ''
            on_number = False
        else:
            scale, increment = number_word_dict[word].scale, number_word_dict[word].increment
            digit_len = max(len(str(increment)), len(str(scale)))

            if digit_len == prev_digit_len:
                if on_number:
                    original = (result_text.strip() + " " + current_text.strip()).strip()
                    number_detected = int(result + current) if float(result + current).is_integer() \
                        else result + current
                    detected_number_list.append(number_detected)
                    detected_original_text_list.append(original)

                result = current = 0
                result_text, current_text = '', ''

            # handle where only scale is mentioned without unit, for ex - thousand(for 1000), hundred(for 100)
            current = 1 if (scale > 0 and current == 0 and increment == 0) else current
            current = current * scale + increment
            current_text = (current_text + " " + word).strip()
            if scale > 1:
                result += current
                result_text = (result_text + " " + current_text).strip()
                current = 0
                current_text = ''
            on_number = True
            prev_digit_len = digit_len

    if on_number:
        original = (result_text.strip() + " " + current_text.strip()).strip()
        number_detected = int(result + current) if float(result + current).is_integer() else result + current
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
