import regex as re
import string

from ner_v2.detectors.numeral.number.number_detection import NumberDetector


def perform_asr_correction(text, pattern_to_match, **kwargs):
    numeric_corrected_output = fix_numerals(text)
    format_match, fuzzcnt = format_adherence_match(numeric_corrected_output, pattern_to_match, **kwargs)
    if not format_match:
        return ""
    punct_processed_output = punct_preprocessing(format_match, pattern_to_match)
    try:
        fuzzy_output = fuzzy_match(punct_processed_output, pattern_to_match, fuzzcnt)
        return fuzzy_output
    except:
        pass
    return punct_processed_output


def format_adherence_match(inp_str, format_str, insert_edits=None, delete_edits=None):
    #TODO: Make search greedy (at the moment it matches smalled output). Will increase latency, but must do.
    if insert_edits:
        if delete_edits:
            form_str = f'(?b)({format_str}){{i<={insert_edits},d<={delete_edits}}}'
        else:
            form_str = f'(?b)({format_str}){{i<={insert_edits}}}'
    else:
        count = lambda l1, l2: sum([1 for x in l1 if x in l2])
        insert_edits = count(inp_str, [" "]) + 2
        form_str = f'(?b)({format_str}){{i<={insert_edits}}}'
    form = re.compile(form_str)
    try:
        m = form.search(inp_str)
        return m.group(), m.fuzzy_counts
    except Exception as e:
        return None, None


puncts = string.punctuation + ' ।'


def punct_preprocessing(inp_str, format_str):
    form = '[' + re.escape(format_str) + ']'
    stray_puncts = re.compile("[" + re.escape(re.sub(form, '', puncts)) + "]")
    temp_text = re.sub(stray_puncts, '', inp_str)
    return temp_text


def fuzzy_match(inp_str, format_str, fuzzyc):
    if re.findall(format_str, inp_str):
        return re.findall(format_str, inp_str)[0]
    if fuzzyc[1]:
        for i in range(len(inp_str)):
            s = (inp_str[:i] + inp_str[i + 1:])
            if re.findall(format_str, s):
                return s


def fix_numerals(text, language='en'):
    temp_text = text
    number_detector = NumberDetector('asr_dummy', language=language)
    detected_numerals, og = number_detector.detect_entity(text=temp_text)
    for num, o in zip(detected_numerals, og):
        sub_reg = re.compile(re.escape(o), re.IGNORECASE)
        temp_text = sub_reg.sub(num['value'], temp_text)
    return temp_text


def fix_email_format(text):
    return re.sub('@?(at)? ?(the)? ?(rate)', '@', text)
