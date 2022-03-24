import regex as re
import string
from six.moves import range

from chatbot_ner.config import ner_logger
from ner_v1.detectors.pattern.regex.data.character_constants import CHARACTER_CONSTANTS
from ner_v2.detectors.numeral.constant import NUMBER_DETECTION_RETURN_DICT_VALUE
from ner_v2.detectors.numeral.number.number_detection import NumberDetector

PUNCTUATION_CHARACTERS = list(string.punctuation + '। ')
EMAIL_CORRECTION_RE = '@? ?(at)? ?(the)? ?(rate)'
AT_SYMBOL = '@'


def edit_distance(string1, string2, insertion_cost=1, deletion_cost=1, substitution_cost=2, max_distance=None):
    """
    Calculate the weighted levenshtein distance between two strings

    Args:
        string1 (unicode): unicode string. If any encoded string type 'str' is passed, it will be decoded using utf-8
        string2 (unicode): unicode string. If any encoded string type 'str' is passed, it will be decoded using utf-8
        insertion_cost (int, optional): cost penalty for insertion operation, defaults to 1
        deletion_cost (int, optional): cost penalty for deletion operation, defaults to 1
        substitution_cost (int, optional): cost penalty for substitution operation, defaults to 2
        max_distance (int, optional): Stop computing edit distance if it grows larger than this argument.
                                      If None complete edit distance is returned. Defaults to None

    For Example:
        edit_distance('hello', 'helllo', max_distance=3)
        >> 1

        edit_distance('beautiful', 'beauty', max_distance=3)
        >> 3

    NOTE: Since, minimum edit distance is time consuming process, we have defined max_distance attribute.
    So, whenever distance exceeds the max_distance the function will break and return the max_distance else
    it will return levenshtein distance
    """
    if isinstance(string1, bytes):
        string1 = string1.decode('utf-8')

    if isinstance(string2, bytes):
        string2 = string2.decode('utf-8')

    if len(string1) > len(string2):
        string1, string2 = string2, string1
    distances = list(range(len(string1) + 1))
    for index2, char2 in enumerate(string2):
        new_distances = [index2 + 1]
        for index1, char1 in enumerate(string1):
            if char1 == char2:
                new_distances.append(distances[index1])
            else:
                new_distances.append(min((distances[index1] + substitution_cost,
                                          distances[index1 + 1] + insertion_cost,
                                          new_distances[-1] + deletion_cost)))
        distances = new_distances
        if max_distance and min(new_distances) > max_distance:
            return max_distance

    return distances[-1]


def fit_text_to_format(input_text, regex_pattern, insert_edits=None):
    """
    Used to modify text to match the given regex pattern.
    Args:
        input_text (str): processed string with numerals and character constants fixed
        regex_pattern (str): pattern to match
        insert_edits (int): number of character deletes allowed for fuzzy matching

    Returns:
        input_text (str): modified text
    """
    if insert_edits:
        pattern = f'(?b)({regex_pattern}){{i<={insert_edits}}}'
    else:
        count = lambda l1, l2: sum([1 for x in l1 if x in l2])
        insert_edits = count(input_text, PUNCTUATION_CHARACTERS) + 2
        pattern = f'(?b)({regex_pattern}){{i<={insert_edits}}}'
    pattern = re.compile(pattern)
    matched_format = pattern.search(input_text)
    if matched_format:
        if any(matched_format.fuzzy_counts):
            fuzzy_edits = matched_format.fuzzy_changes[1]  # Insert edits are returned at position 1 in the tuple
            for corrector, index in enumerate(sorted(fuzzy_edits, reverse=False)):
                index -= corrector
                input_text = _omit_character_by_index(input_text, index)
    return input_text


def _omit_character_by_index(text, index) -> str:
    return text[:index] + text[index + 1:]


def resolve_numerals(text) -> str:
    """
    Uses NumberDetector to resolve numeric occurrences in text for both English and Hindi.
    Args:
        text (str): processed string with numerals and character constants fixed
    Returns:
        processed_text (str): modified text
    """
    processed_text = text
    number_detector = NumberDetector('asr_dummy', language='en')
    detected_numerals, original_texts = number_detector.detect_entity(text=text)
    detected_numerals_hi, original_texts_hi = number_detector.detect_entity(text=text, language='hi')
    detected_numerals.extend(detected_numerals_hi)
    original_texts.extend(original_texts_hi)
    for number, original_text in zip(detected_numerals, original_texts):
        substitution_reg = re.compile(re.escape(original_text), re.IGNORECASE)
        processed_text = substitution_reg.sub(number[NUMBER_DETECTION_RETURN_DICT_VALUE], processed_text)
    return processed_text


def resolve_characters(text) -> str:
    """
    Uses a dictionary to resolve hindi character occurrences in text to English.
    Args:
        text (str): processed string with numerals fixed
    Returns:
        processed_text (str): modified text
    """
    processed_text = text
    occurrences = []
    for char in CHARACTER_CONSTANTS.keys():
        if char in text:
            occurrences.append(char)
    for fragment in sorted(occurrences, key=len):
        processed_text = processed_text.replace(fragment, CHARACTER_CONSTANTS[fragment])
    return processed_text


def perform_asr_correction(input_text, regex_pattern):
    """
    Main function for text normalization for ASR retrieved input.
    Performs resolution for numerics and characters
    and uses fuzzy matching to modify text as per the RegEx provided.

    Example procedure:
        input_text = "बी nine nine three zero"
        regex = "\w\d{4}"

        >> resolve_numerals(input_text)
            "बी 9 9 3 0"
        >> resolve_characters(processed_text)
            "B 9 9 3 0"
        >> fit_text_to_format(processed_text, regex_pattern)
            "B9930"
        Returns:
            'B9930'
    Args:
        input_text (str): original text (as per ASR engine output)
        regex_pattern (str): Regex pattern to match
    Returns:
        processed_text (str): modified text
    """
    processed_text = resolve_numerals(input_text)
    processed_text = resolve_characters(processed_text)
    processed_text = fit_text_to_format(processed_text, regex_pattern)
    return processed_text


def preprocess_asr_email(text):
    """
    Handles common error occurrences in Email ASR

    Args:
        text (str): original text (as per ASR engine output)
    Returns:
        processed_text (str): modified text
    """
    processed_text = re.sub(EMAIL_CORRECTION_RE, AT_SYMBOL, text)
    processed_text = re.sub(' at ', AT_SYMBOL, processed_text)
    return processed_text
