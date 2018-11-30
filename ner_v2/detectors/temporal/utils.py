import calendar
import re
from datetime import datetime, timedelta
import pandas as pd
from ner_v2.detectors.temporal.constant import POSITIVE_TIME_DIFF, NEGATIVE_TIME_DIFF, CONSTANT_FILE_KEY


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
