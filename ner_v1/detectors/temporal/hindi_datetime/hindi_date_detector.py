from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from constant import dates_dict, datetime_dict, numbers_dict
from ner_v1.detectors.temporal.hindi_datetime.constant import REGEX_DATE_REF, REGEX_MONTH_REF, \
    REGEX_TARIKH_MONTH_REF_1, REGEX_TARIKH_MONTH_REF_2, REGEX_TARIKH_MONTH_REF_3, REGEX_AFTER_DAYS_REF, \
    REGEX_WEEKDAY_MONTH_REF_1, REGEX_WEEKDAY_MONTH_REF_2, REGEX_WEEKDAY_REF_1, REGEX_WEEKDAY_REF_2
from ner_v1.detectors.temporal.hindi_datetime.utils import next_weekday, nth_weekday, convert_numeral_to_number


def get_hindi_date(text, today, is_past=False):
    """
    Method to return day, month, year from given hinglish text, Various regular expression has been written to
    capture dates from text like 'kal', 'parso', 'agle mangalvar', 'aane wale month ki 2 tarikh ko'. Each expression is
    ran sequentially over text and return required dd, mm, yy format as soon as given expression matches with text.
    Args:
        text (str): hinglish text containing dates
        today (datetime): python datetime object for today's date
        is_past (bool): Boolean to know if the context of text is in past or in future
    Returns:
        dd (int): day
        mm (int): month
        yy (int): year
    """
    dd = 0
    mm = 0
    yy = 0
    today_mmdd = "%d%02d" % (today.month, today.day)
    today_yymmdd = "%d%02d%02d" % (today.year, today.month, today.day)
    text = convert_numeral_to_number(text)

    # Regex for date like 'kal', 'parso'
    date_ref_match = REGEX_DATE_REF.findall(text)
    if date_ref_match:
        if not is_past:
            r_date = today + timedelta(days=dates_dict[date_ref_match[0]][0])
        else:
            r_date = today - timedelta(days=dates_dict[date_ref_match[0]][0])
        dd, mm, yy = r_date.day, r_date.month, r_date.year
        return dd, mm, yy

    # Regex for date like '2 july', 'pehli august'
    date_month_match = REGEX_MONTH_REF.findall(text)
    if date_month_match:
        date_month_match = date_month_match[0]
        dd = int(date_month_match[0])
        mm = dates_dict[date_month_match[1]][0]
        mmdd = "%02d%02d" % (mm, dd)
        if int(today_mmdd) < int(mmdd):
            yymmdd = str(today.year) + mmdd
            yy = today.year
        else:
            yymmdd = str(today.year + 1) + mmdd
            yy = today.year + 1
        if is_past:
            if int(today_yymmdd) < int(yymmdd):
                yy -= 1
        return dd, mm, yy

    # Regex for date like '2 tarikh is mahine ki'
    tarikh_month_match = REGEX_TARIKH_MONTH_REF_1.findall(text)
    if tarikh_month_match:
        tarikh_month_match = tarikh_month_match[0]
        dd = int(tarikh_month_match[0])
        if tarikh_month_match[2] and tarikh_month_match[3]:
            req_date = today + relativedelta(months=datetime_dict[tarikh_month_match[2]][1])
            mm = req_date.month
            yy = req_date.year
        else:
            mm = today.month
            yy = today.year
        return dd, mm, yy

    # Regex for date like 'agle mahine ki 10 tarikh ko'
    tarikh_month_match = REGEX_TARIKH_MONTH_REF_2.findall(text)
    if tarikh_month_match:
        tarikh_month_match = tarikh_month_match[0]
        dd = int(tarikh_month_match[2])
        if tarikh_month_match[0] and tarikh_month_match[1]:
            req_date = today + relativedelta(months=datetime_dict[tarikh_month_match[0]][1])
            mm = req_date.month
            yy = req_date.year
        else:
            mm = today.month
            yy = today.year
        return dd, mm, yy

    # Regex for date like '2 tarikh ko'
    tarikh_month_match = REGEX_TARIKH_MONTH_REF_3.findall(text)
    if tarikh_month_match:
        c3_match = tarikh_month_match[0]
        dd = int(c3_match[0])
        if today.day < dd:
            mm = today.month
            yy = today.year
        else:
            req_date = today + relativedelta(months=1)
            mm = req_date.month
            yy = req_date.year
        return dd, mm, yy

    # Regex for date like '2 din hua', '2 din baad'
    after_days_match = REGEX_AFTER_DAYS_REF.findall(text)
    if after_days_match:
        after_days_match = after_days_match[0]
        r_date = today + relativedelta(days=numbers_dict[after_days_match[0]][0])
        dd, mm, yy = r_date.day, r_date.month, r_date.year
        return dd, mm, yy

    # Regex for date like '2 tuesday agle month ki', 'teesra mangalvar aane wale month ka'
    weekday_month_match = REGEX_WEEKDAY_MONTH_REF_1.findall(text)
    if weekday_month_match:
        weekday_month_match = weekday_month_match[0]
        n_weekday = int(weekday_month_match[0])
        weekday = dates_dict[weekday_month_match[1]][0]
        ref_date = today + relativedelta(months=datetime_dict[weekday_month_match[2]][1])
        r_date = nth_weekday(n_weekday, weekday, ref_date)
        dd, mm, yy = r_date.day, r_date.month, r_date.year
        return dd, mm, yy

    # Regex for date like 'agle month ka pehla monday', 'pichle month ki 3 shanivar'
    weekday_month_match = REGEX_WEEKDAY_MONTH_REF_2.findall(text)
    if weekday_month_match:
        weekday_month_match = weekday_month_match[0]
        n_weekday = int(weekday_month_match[2])
        weekday = dates_dict[weekday_month_match[3]][0]
        ref_date = today + relativedelta(months=datetime_dict[weekday_month_match[0]][1])
        r_date = nth_weekday(weekday, n_weekday, ref_date)
        dd, mm, yy = r_date.day, r_date.month, r_date.year
        return dd, mm, yy

    # Regex for date like 'aane wala tuesday', 'is mangalvar'
    weekday_ref_match = REGEX_WEEKDAY_REF_1.findall(text)
    if weekday_ref_match:  # [('is', 'tuesday')]
        weekday_ref_match = weekday_ref_match[0]
        n = datetime_dict[weekday_ref_match[0]][1]
        weekday = dates_dict[weekday_ref_match[1]][0]
        r_date = next_weekday(current_date=today, n=n, weekday=weekday)
        dd, mm, yy = r_date.day, r_date.month, r_date.year
        return dd, mm, yy
    # Regex for date like 'monday', 'somvar'
    weekday_ref_match = REGEX_WEEKDAY_REF_2.findall(text)
    if weekday_ref_match:  # ['monday']
        weekday = dates_dict[weekday_ref_match[0]][0]
        r_date = next_weekday(current_date=today, n=0, weekday=weekday)
        dd, mm, yy = r_date.day, r_date.month, r_date.year
        return dd, mm, yy
    return dd, mm, yy
