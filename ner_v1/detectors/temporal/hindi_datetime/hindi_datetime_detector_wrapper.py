from ner_v1.detectors.constant import TYPE_EXACT
from ner_v1.detectors.temporal.hindi_datetime.constant import HINDI_TAGGED_DATE, HINDI_TAGGED_TIME
from ner_v1.detectors.temporal.hindi_datetime.hindi_date_detector import get_hindi_date
from ner_v1.detectors.temporal.hindi_datetime.hindi_date_time_tagger import HindiDateTimeTagger
from ner_v1.detectors.temporal.hindi_datetime.hindi_time_detector import get_hindi_time
from chatbot_ner.config import ner_logger

from datetime import datetime
import re
import pytz


class HindiDateTimeDetector(object):
    """
    A wrapper class to detect hindi datetime from hinglish text
    """
    def __init__(self, message, timezone='UTC', outbound_message=None):
        """
        Initialise parameters
        Args:
            message (str): message
            timezone (str): timezone
            outbound_message (str): previous bot message
        """
        self.message = message
        self.bot_outbound_message = outbound_message
        try:
            self.timezone = pytz.timezone(timezone)
        except Exception as e:
            ner_logger.debug('Timezone error: %s ' % e)
            self.timezone = pytz.timezone('UTC')
            ner_logger.debug('Default timezone passed as "UTC"')
        self.now_date = datetime.now(tz=self.timezone)
        self.datetime_tagger_object = HindiDateTimeTagger()

    @staticmethod
    def return_ner_format_date(dd, mm, yy):
        """
        Method to make detected date params in NER required format
        Args:
            dd (int): day
            mm (int): month
            yy (int): year

        Returns:
            (dict): dictionary with keys
                dd (int): day
                mm (int): month
                yy (int): year
                type (str): date type
        """
        return {
            'dd': dd,
            'mm': mm,
            'yy': yy,
            'type': TYPE_EXACT
        }

    @staticmethod
    def return_ner_format_time(hh, mm, nn):
        """
        Method to make detected date params in NER required format
        Args:
            hh (int): hour
            mm (int): minutes
            nn (str): time type like 'am', 'pm' or df for difference with current time

        Returns:
            (dict): dictionary with keys
                hh (int): hour
                mm (int): minutes
                nn (str): time type
        """
        return {
            'hh': hh,
            'mm': mm,
            'nn': nn
        }

    def is_outbound_message_for_past(self):
        """
        Method to find if previous outbound message is referring to past or future instance so that, correct
        date can be find for text like 'kal', 'parso' as in hindi they are referenced for both past and
        future instances
        Returns:
            (bool): False if there is no previous bot message or reference is for future else True
        """
        if not self.bot_outbound_message:
            return False

        english_past_reference = "tha|thi|"
        hinglish_past_reference = u'थी|था'

        past_reference = english_past_reference + hinglish_past_reference
        past_reference_regex = re.compile(past_reference)

        if past_reference_regex.match(self.bot_outbound_message):
            return True
        else:
            return False

    def tag_date_time(self):
        """
        Method to return dict containing list of date and time tagged and original text from message
        Returns:
            (dict):
                HINDI_TAGGED_DATE (list): list containing list of tagged text and list of original text for date
                HINDI_TAGGED_TIME (list): list containing list of tagged text and list of original text for time
        """
        response = self.datetime_tagger_object.get_datetime_tag_text(self.message)
        return response

    def detect_date(self):
        """
        Method to detect date, month and year from tagged date text
        Returns:
            date_list (list): list of dict containing date, month, year for each detected date
            original_text_list (list): list of original text for each detected date
        """
        date_list = []
        original_text_list = []
        try:
            tagged_datetime_dict = self.tag_date_time()
            is_past_reference = self.is_outbound_message_for_past()
            if len(tagged_datetime_dict[HINDI_TAGGED_DATE]) > 0:
                date_text_list = tagged_datetime_dict[HINDI_TAGGED_DATE][0]
                original_text_date_list = tagged_datetime_dict[HINDI_TAGGED_DATE][1]
                for date_text, original_text in zip(date_text_list, original_text_date_list):
                    dd, mm, yy = get_hindi_date(date_text, self.now_date, is_past=is_past_reference)
                    if dd and mm and yy:
                        date_list.append(self.return_ner_format_date(dd, mm, yy))
                        original_text_list.append(original_text)
        except BaseException as e:
            ner_logger.exception("!! Exception hindi date detection, Error - %s" % str(e))

        return date_list, original_text_list

    def detect_time(self):
        """
        Method to detect date, month and year from tagged date text
        Returns:
            date_list (list): list of dict containing date, month, year for each detected date
            original_text_list (list): list of original text for each detected date
        """
        time_list = []
        original_text_list = []
        try:
            tagged_datetime_dict = self.tag_date_time()

            if len(tagged_datetime_dict[HINDI_TAGGED_TIME]) > 0:
                time_text_list = tagged_datetime_dict[HINDI_TAGGED_TIME][0]
                original_text_time_list = tagged_datetime_dict[HINDI_TAGGED_TIME][1]
                for time_text, original_text in zip(time_text_list, original_text_time_list):
                    hh, mm, nn = get_hindi_time(time_text, self.now_date)
                    if hh and mm:
                        time_list.append(self.return_ner_format_time(hh, mm, nn))
                        original_text_list.append(original_text)
        except BaseException as e:
            ner_logger.exception("!! Exception hindi time detection, Error - %s" % str(e))
        return time_list, original_text_list
