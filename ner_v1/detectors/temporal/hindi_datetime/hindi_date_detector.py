from dateutil.relativedelta import relativedelta
import calendar
import re
from datetime import datetime as dt, timedelta
from ner_v1.detectors.constant import TYPE_EXACT

from constant import dates_dict, datetime_dict, numbers_dict


def convert_number(item):
	"""

	Args:
		item:

	Returns:

	"""
	common = set(item.split()) & set(numbers_dict.keys())
	if common:
		for each in list(common):
			item = re.sub(each, str(numbers_dict[each][0]), item)
	return item


def nth_weekday(weekday, n, ref_date):
	"""

	Args:
		weekday:
		n:
		ref_date:

	Returns:

	"""
	first_day_of_month = dt(ref_date.year, ref_date.month, 1)
	first_weekday = first_day_of_month + timedelta(days=((weekday - calendar.monthrange(
		ref_date.year, ref_date.month)[0]) + 7) % 7)
	return first_weekday + timedelta(days=(n - 1) * 7)


def next_weekday(d, weekday, n):
	"""

	Args:
		d:
		weekday:
		n:

	Returns:

	"""
	days_ahead = weekday - d.weekday()
	if days_ahead < 0:
		n = n + 1 if n == 0 else n
	if days_ahead <= 0:  # Target day already happened this week
		days_ahead += n * 7
	return d + timedelta(days=days_ahead)


date_ref = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'ref_day']) + ")"
day_ref = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'date']) + ")"
tarikh_ref = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] is None]) + ")"
months_ref = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'months']) + ")"
weekday_ref = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'weekday']) + ")"
month_ref = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'month']) + ")"
ref_datetime = "(" + "|".join([x for x in datetime_dict if datetime_dict[x][2] == 0]) + ")"

a1 = re.compile(r'\b' + date_ref + r'\b')
b1 = re.compile(r'(\d+)\s*' + month_ref)

c1 = re.compile(r'(\d+)\s*' + tarikh_ref + '\\s*' + ref_datetime + r'\s*' + months_ref)
c2 = re.compile(ref_datetime + r'\s*' + months_ref + r'\s*(\d+)\s+' + tarikh_ref)
c3 = re.compile(r'(\d+)\s*' + tarikh_ref)

d1 = re.compile(r'(\d+)\s*' + day_ref + r'\s+' + ref_datetime)

e1 = re.compile(r'(\d+)\s*' + weekday_ref + '\\s*' + ref_datetime + r'\s+' + months_ref)
e2 = re.compile(ref_datetime + r'\s+' + months_ref + r'\s+[a-z]*\s*(\d+)\s*' + weekday_ref)

f1 = re.compile(ref_datetime + r'\s*' + weekday_ref)
f2 = re.compile(weekday_ref)


def return_parser_type(dd, mm, yy):
	"""

	Args:
		dd:
		mm:
		yy:

	Returns:

	"""
	return {
		'dd': dd,
		'mm': mm,
		'yy': yy,
		'type': TYPE_EXACT
	}


def get_hindi_date(text, is_past=False):
	"""

	Args:
		text:
		is_past:

	Returns:

	"""
	original_text = None
	dd = 0
	mm = 0
	yy = 0
	today = dt.today()
	today_mmdd = "%d%02d" % (today.month, today.day)
	today_yymmdd = "%d%02d%02d" % (today.year, today.month, today.day)
	raw_text = " " + text + " "
	text = convert_number(text)
	a1_match = a1.findall(text)
	if a1_match:
		original_text = a1_match[0]
		if not is_past:
			r_date = today + timedelta(days=dates_dict[a1_match[0]][0])
		else:
			r_date = today - timedelta(days=dates_dict[a1_match[0]][0])
		dd = r_date.day
		mm = r_date.month
		yy = r_date.year
		return return_parser_type(dd, mm, yy), original_text
	b1_match = b1.findall(text)
	if b1_match:
		b1_match = b1_match[0]
		original_text = " ".join(b1_match)
		dd = int(b1_match[0])
		mm = dates_dict[b1_match[1]][0]
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
		return return_parser_type(dd, mm, yy), original_text
	c1_match = c1.findall(text)
	if c1_match:
		c1_match = c1_match[0]
		original_text = " ".join(c1_match)
		dd = int(c1_match[0])
		if c1_match[2] and c1_match[3]:
			req_date = today + relativedelta(months=datetime_dict[c1_match[2]][1])
			mm = req_date.month
			yy = req_date.year
		else:
			mm = today.month
			yy = today.year
		return return_parser_type(dd, mm, yy), original_text
	c2_match = c2.findall(text)
	if c2_match:
		c2_match = c2_match[0]
		original_text = " ".join(c2_match)
		dd = int(c2_match[2])
		if c2_match[0] and c2_match[1]:
			req_date = today + relativedelta(months=datetime_dict[c2_match[0]][1])
			mm = req_date.month
			yy = req_date.year
		else:
			mm = today.month
			yy = today.year
		return return_parser_type(dd, mm, yy), original_text
	c3_match = c3.findall(text)
	if c3_match:
		c3_match = c3_match[0]
		original_text = " ".join(c3_match)
		dd = int(c3_match[0])
		if today.day < dd:
			mm = today.month
			yy = today.year
		else:
			req_date = today + relativedelta(months=1)
			mm = req_date.month
			yy = req_date.year
		return return_parser_type(dd, mm, yy), original_text
	d1_match = d1.findall(text)
	if d1_match:
		d1_match = d1_match[0]
		original_text = " ".join(d1_match)
		r_date = today + relativedelta(days=datetime_dict[d1_match[2]][1])
		dd = r_date.day
		mm = r_date.month
		yy = r_date.year
		return return_parser_type(dd, mm, yy), original_text
	e1_match = e1.findall(text)
	if e1_match:  # [('2', 'tuesday', 'pichle', 'month')]
		e1_match = e1_match[0]
		original_text = " ".join(e1_match)
		n_weekday = int(e1_match[0])
		weekday = dates_dict[e1_match[1]][0]
		ref_date = today + relativedelta(months=datetime_dict[e1_match[2]][1])
		r_date = nth_weekday(n_weekday, weekday, ref_date)
		dd = r_date.day
		mm = r_date.month
		yy = r_date.year
		return return_parser_type(dd, mm, yy), original_text
	e2_match = e2.findall(text)
	if e2_match:  # [('pichle', 'month', '2', 'tuesday')]
		e2_match = e2_match[0]
		original_text = raw_text.strip()
		n_weekday = int(e2_match[2])
		weekday = dates_dict[e2_match[3]][0]
		ref_date = today + relativedelta(months=datetime_dict[e2_match[0]][1])
		r_date = nth_weekday(weekday, n_weekday, ref_date)
		dd = r_date.day
		mm = r_date.month
		yy = r_date.year
		return return_parser_type(dd, mm, yy), original_text

	f1_match = f1.findall(text)
	if f1_match:  # [('is', 'tuesday')]
		f1_match = f1_match[0]
		original_text = " ".join(f1_match)
		n = datetime_dict[f1_match[0]][1]
		weekday = dates_dict[f1_match[1]][0]
		r_date = next_weekday(d=today, n=n, weekday=weekday)
		dd = r_date.day
		mm = r_date.month
		yy = r_date.year
		return return_parser_type(dd, mm, yy), original_text

	f2_match = f2.findall(text)
	if f2_match:  # ['monday']
		original_text = " ".join(f2_match)
		weekday = dates_dict[f2_match[0]][0]
		r_date = next_weekday(d=today, n=0, weekday=weekday)
		dd = r_date.day
		mm = r_date.month
		yy = r_date.year
		return return_parser_type(dd, mm, yy), original_text
	return return_parser_type(dd, mm, yy), original_text
