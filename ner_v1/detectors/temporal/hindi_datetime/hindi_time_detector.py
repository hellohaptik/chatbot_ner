from datetime import datetime, timedelta

from ner_v1.detectors.temporal.hindi_datetime.constant import REGEX_HOUR_TIME_1, REGEX_MINUTE_TIME_1, \
    REGEX_HOUR_TIME_2, MINUTE_TIME_REGEX_2, datetime_dict, DAYTIME_MERIDIAN, IGNORE_DIFF_HOUR_LIST
from utils import convert_numeral_to_number, get_hour_min_diff


def get_hindi_time(text, today):
    """
    Method to return hour, minute, time type from given hinglish text, Various regular expression has been written to
    capture time from text like '2 baje', '2 ghante baad', 'subah me dhaai baje'. Each expressions is
    ran sequentially over text and return required hh, mm, nn format as soon as given expression matches with text.
    Args:
        text (str): hinglish text in which time text is present
        today (datetime):  python datetime object for current time
    Returns:
        hh (int): hours
        mm (int): minutes
        nn (str): time type like df
    """
    hh = 0
    mm = 0
    nn = None
    text = " " + text + " "
    text = convert_numeral_to_number(text)

    # regex to match text like '2 bje', 'teen bajkar', '2 ghante baad'
    regex_hour_match = REGEX_HOUR_TIME_1.findall(text)
    if regex_hour_match:
        regex_hour_match = regex_hour_match[0]
        hh = int(regex_hour_match[1])
        if regex_hour_match[0]:
            val_add = datetime_dict[regex_hour_match[0]][1]
            hh = hh + val_add
        if regex_hour_match[3] and regex_hour_match[2] not in IGNORE_DIFF_HOUR_LIST:
            ref_date = today + datetime_dict[regex_hour_match[3]][1] * timedelta(hours=hh)
            return get_hour_min_diff(today, ref_date)

    # regex to match text like '30 minutes', '12 minute pehle'
    regex_minute_match = REGEX_MINUTE_TIME_1.findall(text)
    if regex_minute_match:
        regex_minute_match = regex_minute_match[0]
        mm = int(regex_minute_match[1])
        if regex_minute_match[3]:
            ref_date = today + datetime_dict[regex_minute_match[3]][1] * timedelta(hours=hh, minutes=mm)
            return get_hour_min_diff(today, ref_date)

    if not (hh or mm):

        # regex to match text like 'dhaai baje', 'saade ek baje', 'aadhe ghante baad'
        regex_hour_match = REGEX_HOUR_TIME_2.findall(text)
        if regex_hour_match:
            regex_hour_match = regex_hour_match[0]
            hh = datetime_dict[regex_hour_match[0]][1]
            if regex_hour_match[2]:
                ref_date = today + datetime_dict[regex_hour_match[2]][1] * timedelta(hours=hh)
                return get_hour_min_diff(today, ref_date)

        # regex to match text like 'dhaai minute baad', 'paune ek baje'
        regex_minute_match = MINUTE_TIME_REGEX_2.findall(text)
        if regex_minute_match:
            regex_minute_match = regex_minute_match[0]
            mm = datetime_dict[regex_minute_match[0]][1]
            if regex_minute_match[2]:
                ref_date = today + datetime_dict[regex_minute_match[2]][1] * timedelta(hours=hh, minutes=mm)
                return get_hour_min_diff(today, ref_date)

    for each in DAYTIME_MERIDIAN:
        if each in text:
            nn = DAYTIME_MERIDIAN[each]

    if type(hh) == float:
        mm = int((hh - int(hh)) * 60)
        hh = int(hh)

    return hh, mm, nn
