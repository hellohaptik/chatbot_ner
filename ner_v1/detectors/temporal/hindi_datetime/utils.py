import calendar
import re
from datetime import datetime, timedelta

from constant import numbers_dict
from ner_v1.constant import POSITIVE_TIME_DIFF, NEGATIVE_TIME_DIFF


def convert_numeral_to_number(text):
    """
    Method to convert numeral present in text to numeric digites
    Args:
        text (str): text string containing numerals

    Returns:
        text (str): text with numeral replaced with numeric

    Examples:
        >> convert_numeral_to_number('teesri tarikh ko')
        >> '3 tarikh ko'

    """
    common = set(text.split()) & set(numbers_dict.keys())
    if common:
        for each in list(common):
            text = re.sub(each, str(numbers_dict[each][0]), text)
    return text


def nth_weekday(weekday, n, ref_date):
    """
    Method to return python datetime object for given nth weekday w.r.t ref_date (reference date)
    Args:
        weekday (int): int count of weekday like 0 for monday, 1 for tuesday
        n (int): nth weekday
        ref_date (datetime): python datetime object for reference

    Returns:
        (datetime): Return required datetime object
    """
    first_day_of_month = datetime(ref_date.year, ref_date.month, 1)
    first_weekday = first_day_of_month + timedelta(days=((weekday - calendar.monthrange(
        ref_date.year, ref_date.month)[0]) + 7) % 7)
    return first_weekday + timedelta(days=(n - 1) * 7)


def next_weekday(current_date, weekday, n):
    """
    Method to return python datetime object to find next weekday from current date
    Args:
        current_date (datetime): python datetime object
        weekday (int): int count of weekday like 0 for monday, 1 for tuesday
        n (int): 0 for coming weekday, 1 for next weekday, 2 for next to next weekday

    Returns:

    """
    days_ahead = weekday - current_date.weekday()
    if days_ahead < 0:
        n = n + 1 if n == 0 else n
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += n * 7
    return current_date + timedelta(days=days_ahead)


def get_hour_min_diff(time1, time2):
    """
    Method to return difference between two times in hours and minutes.
    Args:
        time1 (datetime): datetime object
        time2 (datetime): datetime object
    Returns:
        hh (int): hour difference between two times
        mm (int): minute difference between two times
        nn (str): tell whether time difference is positive or negative
    """
    nn = POSITIVE_TIME_DIFF
    if time2 > time1:
        diff = time2 - time1
    else:
        diff = time1 - time2
        nn = NEGATIVE_TIME_DIFF
    minutes = (diff.seconds / 60) % 60
    hours = diff.seconds / 3600
    return hours, minutes, nn
