from ner_v1.detectors.constant import TYPE_EXACT
from ner_v1.detectors.temporal.hindi_datetime.constant import HINDI_TAGGED_DATE, HINDI_TAGGED_TIME
from ner_v1.detectors.temporal.hindi_datetime.hindi_date_detector import get_hindi_date
from ner_v1.detectors.temporal.hindi_datetime.hindi_date_time_tagger import HindiDateTimeTagger
from ner_v1.detectors.temporal.hindi_datetime.hindi_time_detector import get_hindi_time


class HindiDateTimeDetector(object):

    def __init__(self, message, now_date, outbound_message=None):
        self.message = message
        self.bot_outbound_message = outbound_message
        self.now_date = now_date
        self.datetime_tagger_object = HindiDateTimeTagger()

    def return_parse_date(self, dd, mm, yy):
        return {
            'dd': dd,
            'mm': mm,
            'yy': yy,
            'type': TYPE_EXACT
        }

    def return_parse_time(self, hh, mm, nn):
        return {
            'hh': hh,
            'mm': mm,
            'nn': nn
        }

    def tag_date_time(self):
        response = self.datetime_tagger_object.get_datetime_tag_text(self.message)
        return response

    def detect_date(self):
        date_list = []
        original_text_list = []
        tagged_datetime_dict = self.tag_date_time()

        if len(tagged_datetime_dict[HINDI_TAGGED_DATE]) > 0:
            date_text_list = tagged_datetime_dict[HINDI_TAGGED_DATE][0]
            original_text_date_list = tagged_datetime_dict[HINDI_TAGGED_DATE][1]
            for date_text, original_text in zip(date_text_list, original_text_date_list):
                dd, mm, yy = get_hindi_date(date_text, self.now_date)
                if dd and mm and yy:
                    date_list.append(self.return_parse_date(dd, mm, yy))
                    original_text_list.append(original_text)

        return date_list, original_text_list

    def detect_time(self):
        time_list = []
        original_text_list = []
        tagged_datetime_dict = self.tag_date_time()

        if len(tagged_datetime_dict[HINDI_TAGGED_TIME]) > 0:
            time_text_list = tagged_datetime_dict[HINDI_TAGGED_TIME][0]
            original_text_time_list = tagged_datetime_dict[HINDI_TAGGED_TIME][1]
            for time_text, original_text in zip(time_text_list, original_text_time_list):
                hh, mm, nn = get_hindi_time(time_text, self.now_date)
                if hh and mm:
                    time_list.append(self.return_parse_time(hh, mm, nn))
                    original_text_list.append(original_text)

        return time_list, original_text_list
