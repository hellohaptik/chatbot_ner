import re

# Dict to detect date in text, 1 dimension determine the magnitude and second dimension decide its day category
dates_dict = {'aaj': [0, "ref_day"], 'kal': [1, "ref_day"], 'parson': [2, "ref_day"], 'narson': [3, "ref_day"],
              'parso': [2, "ref_day"], 'narso': [3, "ref_day"], 'tareekh': [0, None],
              'din': [0, "date"], 'dino': [0, "day"], 'month': [0, "months"], 'tarikh': [0, None],
              'mahine': [0, "months"], 'mahina': [0, "months"], 'monday': [0, "weekday"], 'tuesday': [1, "weekday"],
              'wednesday': [2, "weekday"], 'thursday': [3, "weekday"], 'friday': [4, "weekday"],
              'saturday': [5, "weekday"], 'sunday': [6, "weekday"], 'somvar': [0, "weekday"], 'somwar': [0, "weekday"],
              'mangalvar': [1, "weekday"], 'mangalwar': [1, "weekday"], 'budhvar': [2, "weekday"],
              'budhwar': [2, "weekday"], 'guruvar': [3, "weekday"], 'guruwar': [3, "weekday"],
              'shukravar': [4, "weekday"], 'shukrawar': [4, "weekday"], 'sukravar': [4, "weekday"],
              'sukrawar': [4, "weekday"], 'shanivar': [5, "weekday"], 'shaniwar': [5, "weekday"],
              'sanivar': [5, "weekday"], 'saniwar': [5, "weekday"], 'ravivar': [6, "weekday"],
              'raviwar': [6, "weekday"],
              'january': [1, "month"], 'february': [2, "month"], 'march': [3, "month"], 'april': [4, "month"],
              'may': [5, "month"], 'june': [6, "month"], 'july': [7, "month"], 'august': [8, "month"],
              'september': [9, "month"], 'october': [10, "month"], 'november': [11, "month"],
              'december': [12, "month"], 'itwar': [6, "weekday"], 'itvar': [6, "weekday"],
              'jan': [1, "month"], 'feb': [2, "month"], 'mar': [3, "month"], 'apr': [4, "month"],
              'jun': [6, "month"], 'jul': [7, "month"], 'aug': [8, "month"],
              'sep': [9, "month"], 'sept': [9, "month"], 'oct': [10, "month"], 'nov': [11, "month"],
              'dec': [12, "month"],
              }

# dict to detect time where keys define tag text and value define category like if its defining hour, minute or second
times_dict = {'abhi': 0, 'turant': 0, 'bje': 1, 'bajkr': 1, 'bajkar': 1, 'baje': 1, 'baj': 1, 'ghante': 1, 'ghanta': 1,
              'ghanton': 1, 'subah': 0, 'shaam': 0, 'sandhya': 0, 'dopahar': 0, 'raat': 0, 'minutes': 2, 'minute': 2,
              'mins': 2, 'min': 2, 'seconds': 3, 'second': 3, 'sec': 3}

# dict to detect reference both date and time, 1st index corresponds to whether it should be added to forward
# or backward entity, 2nd index is for magnitude of addition or deletion from entity and 3rd index is to differentiate
# if given key have exact(dedh, dhaai) or diff(baad, pichhle) or reference (saade, paune) magnitude

datetime_dict = {"baad": (-1, 1, 0), "is": (1, 0, 0), "isi": (1, 0, 0), "pahle": (-1, -1, 0), "pehle": (-1, -1, 0),
                 "phle": (-1, -1, 0), "pichhle": (1, -1, 0), "hua": (-1, -1, 0), "pichhla": (1, -1, 0),
                 "pichle": (1, -1, 0),  "pichla": (1, -1, 0), "ane": (1, 1, 0), "aane": (1, 1, 0), "wala": (1, 1, 0),
                 "vala": (1, 1, 0), "wale": (1, 1, 0), "vale": (1, 1, 0), "wali": (1, 1, 0), "vali": (1, 1, 0),
                 "hue": (-1, -1, 0), "agle": (1, 1, 0), "agla": (1, 1, 0), "agli": (1, 1, 0),
                 "ane wala": (1, 1, 0), "aane wala": (1, 1, 0), "aane vala": (1, 1, 0), "ane vala": (1, 1, 0),
                 "ane vale": (1, 1, 0), "ane wale": (1, 1, 0), "ane vali": (1, 1, 0), "ane wali": (1, 1, 0),
                 "aadhe": (1, 0.5, 1), "aadha": (1, 0.5, 1), "dedh": (1, 1.5, 1), "dhaai": (1, 2.5, 1),
                 "saade": (1, 0.5, 2), 'me': (-1, 1, 0), 'paune': (1, -0.25, 2),
                 'sawa': (1, 0.25, 2), 'sava': (1, 0.25, 2), 'pehla': (-1, -1, 0)}

# dict to contain numbers and hindi numerals, 1st index define magnitude and second define which entity is should be
# added to (forward or backward)
numbers_dict = {'1': [1, 1], 'ek': [1, 1], 'pahla': [1, 1], 'pahli': [1, 1], 'pehle': [1, 1], 'pehla': [1, 1],
                '2': [2, 1], 'do': [2, 1],
                'doosra': [2, 1], 'doosri': [2, 1], 'doosre': [2, 1], '3': [3, 1], 'teen': [3, 1], 'teesra': [3, 1],
                'teesre': [3, 1], 'teesri': [3, 1], '4': [4, 1], 'chaar': [4, 1], 'chauthi': [4, 1], 'chautha': [4, 1],
                'char': [4, 1], 'choutha': [4, 1], 'chauthe': [4, 1], '5': [5, 1], 'paanch': [5, 1],
                'paanchva': [5, 1], 'paanchve': [5, 1],
                'paanchvi': [5, 1], '6': [6, 1], 'chhatvi': [6, 1], 'chhathva': [6, 1], 'chhathvi': [6, 1],
                'chhatve': [6, 1], 'chhe': [6, 1], 'chhata': [6, 1], '7': [7, 1], 'saat': [7, 1],
                'saatva': [7, 1], 'saatvi': [7, 1], 'saatve': [7, 1],
                '8': [8, 1], 'aathvi': [8, 1], 'aath': [8, 1], 'aathva': [8, 1], 'aathve': [8, 1],
                '9': [9, 1], 'nau': [9, 1], 'nauve': [9, 1],
                'naumi': [9, 1], 'nauvi': [9, 1], 'nauva': [9, 1], 'nahla': [9, 1], '10': [10, 1], 'dasvi': [10, 1],
                'dasve': [10, 1],
                'das': [10, 1], 'dasva': [10, 1], '11': [11, 1], 'gyarah': [11, 1], 'gyarva': [11, 1], '12': [12, 1],
                'barah': [12, 1], 'barvan': [12, 1], '13': [13, 1], 'terah': [13, 1], '14': [14, 1],
                'chaudah': [14, 1], '15': [15, 1], 'pandrah': [15, 1], '16': [16, 1], 'solah': [16, 1], '17': [17, 1],
                'satrah': [17, 1], '18': [18, 1], 'atharah': [18, 1], '19': [19, 1], 'unnish': [19, 1], '20': [20, 1],
                'bees': [20, 1], '21': [21, 1], 'ikkish': [21, 1], '22': [22, 1], 'baaish': [22, 1], '23': [23, 1],
                'teish': [23, 1], '24': [24, 1], 'chaubish': [24, 1], '25': [25, 1], 'pachhish': [25, 1],
                '26': [26, 1], 'chhabish': [26, 1], '27': [27, 1], 'sattaish': [27, 1], '28': [28, 1],
                'atthaish': [28, 1], '29': [29, 1], 'untish': [29, 1], '30': [30, 1], 'teesh': [30, 1],
                '31': [31, 1], 'ikattish': [31, 1]}

# word to separate two date time
separators = {'se': 0, 'ke': 0, 'aur': 0, 'evam': 0, 'lekin': 0, 'par': 0, 'magar': 0, 'kintu': 0, 'parantu': 0,
              'ya': 0, 'kyunki': 0, 'isliye': 0}

# dict to find meridian for time detected
DAYTIME_MERIDIAN = {
    'am': 'am',
    'pm': 'pm',
    'subah': 'am',
    'raat': 'pm',
    'dopahar': 'pm',
    'din': 'pm',
    'shaam': 'pm',
    'sandhya': 'pm'
}

# words when diff is ignored
IGNORE_DIFF_HOUR_LIST = ["bje", "baje", "bajkar", "bajkr", "baj"]

# tag word for word like 'baad', 'pichhle' to decide it should be added (either forward or backward entity)
TAG_PREV = 'prev'
TAG_NEXT = 'next'

# dict key for datetime tagger
HINDI_TAGGED_DATE = 'date'
HINDI_TAGGED_TIME = 'time'


# Time detector Regex
REF_EXACT_TIME = "(" + "|".join([x for x in datetime_dict if datetime_dict[x][2] == 1]) + ")"
REF_DIFF_TIME = "(" + "|".join([x for x in datetime_dict if datetime_dict[x][2] == 0]) + "|)"
REF_ADD_TIME = "(" + "|".join([x for x in datetime_dict if datetime_dict[x][2] == 2]) + "|)"

HOUR_VARIANTS = "(" + "|".join([x for x in times_dict if times_dict[x] == 1]) + ")"
MINUTE_VARIANTS = "(" + "|".join([x for x in times_dict if times_dict[x] == 2]) + ")"

REGEX_HOUR_TIME_1 = re.compile(REF_ADD_TIME + r"\s*(\d+)\s*" + HOUR_VARIANTS + r"\s+" + REF_DIFF_TIME)
REGEX_MINUTE_TIME_1 = re.compile(REF_ADD_TIME + r"\s*(\d+)\s*" + MINUTE_VARIANTS + r"\s+" + REF_DIFF_TIME)
REGEX_HOUR_TIME_2 = re.compile(REF_EXACT_TIME + r"\s*" + HOUR_VARIANTS + r"\s+" + REF_DIFF_TIME)
MINUTE_TIME_REGEX_2 = re.compile(REF_EXACT_TIME + r"\s*" + MINUTE_VARIANTS + r"\s+" + REF_DIFF_TIME)


# Date detector Regex
DATE_REF = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'ref_day']) + ")"
DAY_REF = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'date']) + ")"
TARIKH_REF = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] is None]) + ")"
MONTHS_TEXT_REF = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'months']) + ")"
WEEKDAY_REF = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'weekday']) + ")"
MONTH_REF = "(" + "|".join([x for x in dates_dict if dates_dict[x][1] == 'month']) + ")"
DATETIME_REF = "(" + "|".join([x for x in datetime_dict if datetime_dict[x][2] == 0]) + ")"

REGEX_DATE_REF = re.compile(r'\b' + DATE_REF + r'\b')
REGEX_MONTH_REF = re.compile(r'(\d+)\s*' + MONTH_REF)
REGEX_TARIKH_MONTH_REF_1 = re.compile(r'(\d+)\s*' + TARIKH_REF + '\\s*' + DATETIME_REF + r'\s*' + MONTHS_TEXT_REF)
REGEX_TARIKH_MONTH_REF_2 = re.compile(DATETIME_REF + r'\s*' + MONTHS_TEXT_REF + r'\s*(\d+)\s+' + TARIKH_REF)
REGEX_TARIKH_MONTH_REF_3 = re.compile(r'(\d+)\s*' + TARIKH_REF)
REGEX_AFTER_DAYS_REF = re.compile(r'(\d+)\s*' + DAY_REF + r'\s+' + DATETIME_REF)
REGEX_WEEKDAY_MONTH_REF_1 = re.compile(r'(\d+)\s*' + WEEKDAY_REF + '\\s*' + DATETIME_REF + r'\s+' + MONTHS_TEXT_REF)
REGEX_WEEKDAY_MONTH_REF_2 = re.compile(DATETIME_REF + r'\s+' + MONTHS_TEXT_REF + r'\s*(\d+)\s*' + WEEKDAY_REF)
REGEX_WEEKDAY_REF_1 = re.compile(DATETIME_REF + r'\s*' + WEEKDAY_REF)
REGEX_WEEKDAY_REF_2 = re.compile(WEEKDAY_REF)
