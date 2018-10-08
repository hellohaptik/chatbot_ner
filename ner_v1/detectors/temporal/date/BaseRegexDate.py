from constant import DATE_CONSTANT_FILE, TIME_CONSTANT_FILE, DATETIME_CONSTANT_FILE, NUMERALS_CONSTANT_FILE
import pandas as pd
import re


class BaseRegexDate(object):

    def __init__(self, data_dir_path):
        # Read date file
        date_constant_df = pd.read_csv(data_dir_path.rstrip('/') + '/' + DATE_CONSTANT_FILE)
        time_constant_df = pd.read_csv(data_dir_path.rstrip('/') + '/' + TIME_CONSTANT_FILE)
        datetime_constant_df = pd.read_csv(data_dir_path.rstrip('/') + '/' + DATETIME_CONSTANT_FILE)
        numeral_constant_df = pd.read_csv(data_dir_path.rstrip('/') + '/' + NUMERALS_CONSTANT_FILE)

        # Time detector Regex

        REF_EXACT_TIME = "(" + "|".join([x for x in date_constant_df if date_constant_df[x][2] == 1]) + ")"
        REF_DIFF_TIME = "(" + "|".join([x for x in time_constant_df if time_constant_df[x][2] == 0]) + "|)"
        REF_ADD_TIME = "(" + "|".join([x for x in datetime_constant_df if numeral_constant_df[x][2] == 2]) + "|)"

        HOUR_VARIANTS = "(" + "|".join([x for x in time_constant_df if time_constant_df[x] == 1]) + ")"
        MINUTE_VARIANTS = "(" + "|".join([x for x in time_constant_df if time_constant_df[x] == 2]) + ")"

        self.REGEX_HOUR_TIME_1 = re.compile(REF_ADD_TIME + r"\s*(\d+)\s*" + HOUR_VARIANTS + r"\s+" + REF_DIFF_TIME)
        self.REGEX_MINUTE_TIME_1 = re.compile(REF_ADD_TIME + r"\s*(\d+)\s*" + MINUTE_VARIANTS + r"\s+" + REF_DIFF_TIME)
        self.REGEX_HOUR_TIME_2 = re.compile(REF_EXACT_TIME + r"\s*" + HOUR_VARIANTS + r"\s+" + REF_DIFF_TIME)
        self.MINUTE_TIME_REGEX_2 = re.compile(REF_EXACT_TIME + r"\s*" + MINUTE_VARIANTS + r"\s+" + REF_DIFF_TIME)

    # parser function for self.REGEX_HOUR_TIME_1
    def parser_regex_hour_time_1(self):
        pass

    # parser function for self.REGEX_HOUR_TIME_2
    def parser_regex_hour_time_2(self):
        pass
