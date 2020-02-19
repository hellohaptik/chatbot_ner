from __future__ import absolute_import
import calendar
from datetime import datetime, timedelta, tzinfo  # FIXME: Change import to `import datetime`

import pandas as pd
import pytz
import six

from chatbot_ner.config import ner_logger
from ner_v2.detectors.temporal.constant import POSITIVE_TIME_DIFF, NEGATIVE_TIME_DIFF, CONSTANT_FILE_KEY
from six.moves import range

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
        (datetime): next weekday datetime from current date
    """
    days_ahead = weekday - current_date.weekday()
    if days_ahead < 0:
        n = n + 1
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


def get_tuple_dict(csv_file):
    """
    Method to convert language constant csv into tuple dict

    Args:
        csv_file (str): csv file path

    Returns:
        (dict): dict containing key as csv index key and all other rows values as tuple
    """
    data_df = pd.read_csv(csv_file, encoding='utf-8')
    data_df = data_df.set_index(CONSTANT_FILE_KEY)
    records = data_df.to_records()
    tuple_records = {}
    for record in records:
        keys = record[0]
        keys = [x.strip().lower() for x in keys.split("|") if x.strip() != ""]
        for key in keys:
            tuple_records[key] = tuple(list(record)[1:])
    return tuple_records


def get_weekdays_for_month(weeknumber, month, year):
    """
    Return list of day for given weeknumber of given month and year

    Args:
        weeknumber (int): week number
        month (int): month
        year (int): year

    Returns:
        (list): list of days
    """
    calendar_month = calendar.monthcalendar(year, month)
    if weeknumber == -1:
        return [day for day in calendar_month[-1] if day != 0]
    elif 0 < weeknumber <= len(calendar_month):
        return [day for day in calendar_month[weeknumber - 1] if day != 0]
    return []


def is_valid_date(dd, mm, yy, tz=None):
    # type: (int, int, int, 'pytz.tzfile.*') -> bool
    """
    Given dd, mm, yy check if it is a valid date in a year

    Args:
        dd (int): upto 2 digit integer
        mm (int): upto 2 digit integer
        yy (int): upto 4 digit integer
        tz (pytz.tzfile.*, optional): A valid pytz timezone. defaults to None

    Returns:
        bool: if dd/mm/yy is a valid date

    Raises:
        TypeError: when any of dd, mm, yy is not an int
    """
    if dd and mm and yy:
        try:
            dt = datetime(year=yy, month=mm, day=dd)
            if tz:
                tz.localize(dt)
            return True
        except (ValueError, AttributeError):
            pass
    return False


def get_previous_month_number(mm, yy):
    # type: (int, int) -> Tuple[int, int]
    """
    Given month number and year get previous month number and adjust year if we flow into previous year

    Args:
        mm (int): upto 2 digit month number, between 1 and 12
        yy (int): any year

    Returns:
        tuple: tuple containing
            int: previous month number after mm
            int: adjusted year for the previous month number

    Raises:
        ValueError: when mm is not between 1 and 12

    """
    if 1 <= mm <= 12:
        if mm == 1:
            mm = 12
            yy -= 1
        else:
            mm -= 1
    else:
        raise ValueError('mm should be between 1 and 12 inclusive')

    return mm, yy


def get_next_month_number(mm, yy):
    # type: (int, int) -> Tuple[int, int]
    """
    Given month number and year get next month number and adjust year if we flow into next year

    Args:
        mm (int): upto 2 digit month number, between 1 and 12
        yy (int): any year

    Returns:
        tuple: tuple containing
            int: next month number after mm
            int: adjusted year for the next month number

    Raises:
        ValueError: when mm is not between 1 and 12

    """
    if 1 <= mm <= 12:
        if mm == 12:
            mm = 1
            yy += 1
        else:
            mm += 1
    else:
        raise ValueError('mm should be between 1 and 12 inclusive')

    return mm, yy


def get_previous_date_with_dd(dd, before_datetime):
    # type: (int, datetime.datetime) -> Tuple[Optional[int], Optional[int], Optional[int]]
    """
    Get closest date with day same as `dd` on or before `before_datetime`

    Args:
        dd (int): 2 digit int, expected between 1 and 31
        before_datetime (datetime.datetime): python datetime object, the date to look back from

    Returns:
        tuple: tuple containing
            int or None: day part of found date, if no such valid date can be found None
            int or None: month part of found date, if no such valid date can be found None
            int or None: year part of found date, if no such valid date can be found None

    """

    end_dd = before_datetime.day
    mm = before_datetime.month
    yy = before_datetime.year

    if dd > end_dd:
        mm, yy = get_previous_month_number(mm=mm, yy=yy)

    # Try in previous three months, it should be possible to get closest valid date with same dd in last 3 months
    for _ in range(3):
        if is_valid_date(dd=dd, mm=mm, yy=yy):
            return dd, mm, yy
        mm, yy = get_previous_month_number(mm=mm, yy=yy)

    return None, None, None


def get_next_date_with_dd(dd, after_datetime):
    # type: (int, datetime.datetime) -> Tuple[Optional[int], Optional[int], Optional[int]]
    """
    Get closest date with day same as `dd` on or after `after_datetime`

    Args:
        dd (int): 2 digit int, expected between 1 and 31
        after_datetime (datetime.datetime): python datetime object, the date to look ahead from

    Returns:
        tuple: tuple containing
            int or None: day part of found date, if no such valid date can be found None
            int or None: month part of found date, if no such valid date can be found None
            int or None: year part of found date, if no such valid date can be found None

    """
    start_dd = after_datetime.day
    mm = after_datetime.month
    yy = after_datetime.year

    if dd < start_dd:
        mm, yy = get_next_month_number(mm=mm, yy=yy)

    # Try in next three months, it should be possible to get closest valid date with same dd in next 3 months
    for _ in range(3):
        if is_valid_date(dd=dd, mm=mm, yy=yy):
            return dd, mm, yy
        mm, yy = get_next_month_number(mm=mm, yy=yy)

    return None, None, None


def get_timezone(timezone, ignore_errors=False):
    # type: (Union[datetime.tzinfo, str, unicode], bool) -> datetime.tzinfo
    """
    Return a datetime.tzinfo (pytz timezone object). If `timezone` is a str, try constructing a pytz
    timezone object with it. If an invalid timezone is mentioned and `ignore_errors` is True, an UTC timezone object
    will be returned. If `timezone` is already a datetime.tzinfo object it will be returned as is

    Args:
        timezone (str or datetime.tzinfo): Either a valid timezone string or datetime.tzinfo object
        ignore_errors (bool, optional): when set to True, ignore errors and return a pytz.UTC when error occurs. When
            set to False, raise exception when invalid timezone is given. Defaults to False.

    Returns:
        datetime.tzinfo: A pytz timezone object

    """
    if (not isinstance(timezone, six.string_types) and
            isinstance(timezone, tzinfo) and
            hasattr(timezone, 'localize')):
        return timezone

    try:
        timezone = pytz.timezone(timezone)
    except Exception as e:
        if ignore_errors:
            ner_logger.debug('Timezone error: %s ' % e)
            timezone = pytz.timezone('UTC')
            ner_logger.debug('Using "UTC" as default timezone')
        else:
            return None
    return timezone


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