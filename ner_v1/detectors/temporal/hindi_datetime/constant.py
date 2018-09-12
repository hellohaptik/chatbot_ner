dates_dict = {'aaj': [0, "ref_day"], 'kal': [1, "ref_day"], 'parson': [2, "ref_day"], 'narson': [3, "ref_day"],
              'din': [0, "date"], 'dino': [0, "day"], 'month': [0, "months"], 'tarikh': [0, None], 'tareekh': [0, None],
              'mahine': [0, "months"], 'mahina': [0, "months"], 'monday': [0, "weekday"], 'tuesday': [1, "weekday"],
              'wednesday': [2, "weekday"], 'thursday': [3, "weekday"], 'friday': [4, "weekday"],
              'saturday': [5, "weekday"], 'sunday': [6, "weekday"], 'somvar': [0, "weekday"],
              'mangalvar': [1, "weekday"], 'budhvar': [2, "weekday"], 'guruvar': [3, "weekday"],
              'shukravar': [4, "weekday"], 'shanivar': [5, "weekday"], 'ravivar': [6, "weekday"],
              'january': [1, "month"], 'february': [2, "month"], 'march': [3, "month"], 'april': [4, "month"],
              'may': [5, "month"], 'june': [6, "month"], 'july': [7, "month"], 'august': [8, "month"],
              'september': [9, "month"], 'october': [10, "month"], 'november': [11, "month"],
              'december': [12, "month"]}

times_dict = {'abhi': 0, 'turant': 0, 'bje': 1, 'bajkr': 1, 'bajkar': 1, 'baje': 1, 'baj': 1, 'ghante': 1, 'ghanta': 1,
              'ghanton': 1, 'subah': 0, 'shaam': 0, 'sandhya': 0, 'dopahar': 0, 'raat': 0, 'minutes': 2, 'minute': 2,
              'mins': 2, 'min': 2, 'seconds': 3, 'second': 3, 'sec': 3}

datetime_dict = {"baad": (-1, 1, 0), "is": (1, 0, 0), "isi": (1, 0, 0), "pahle": (-1, -1, 0), "pehle": (-1, -1, 0),
                 "phle": (-1, -1, 0), "pichle": (1, -1, 0), "hua": (-1, -1, 0),
                 "hue": (-1, -1, 0), "agle": (1, 1, 0), "agla": (1, 1, 0), "agli": (1, 1, 0),
                 "ane wala": (1, 1, 0), "aane wala": (1, 1, 0), "aane vala": (1, 1, 0), "ane vala": (1, 1, 0),
                 "aadhe": (1, 0.5, 1), "aadha": (1, 0.5, 1), "dedh": (1, 1.5, 1), "dhaai": (1, 2.5, 1),
                 "saade": (1, 0.5, 2), 'me': (-1, 1, 0), 'paune': (1, -0.25, 2),
                 'sawa': (1, 0.25, 2), 'sava': (1, 0.25, 2)}

numbers_dict = {'1': [1, 1], 'ek': [1, 1], 'pahla': [1, 1], 'pahli': [1, 1], '2': [2, 1], 'do': [2, 1],
                'doosra': [2, 1], '3': [3, 1], 'teen': [3, 1], 'teesra': [3, 1], '4': [4, 1], 'chaar': [4, 1],
                'char': [4, 1], 'choutha': [4, 1], '5': [5, 1], 'paanch': [5, 1], 'paanchva': [5, 1], '6': [6, 1],
                'chhe': [6, 1], 'chhata': [6, 1], '7': [7, 1], 'saat': [7, 1], 'saatva': [7, 1], '8': [8, 1],
                'aath': [8, 1], 'aathva': [8, 1], '9': [9, 1], 'nau': [9, 1], 'nahla': [9, 1], '10': [10, 1],
                'das': [10, 1], 'dasva': [10, 1], '11': [11, 1], 'gyarah': [11, 1], 'gyarva': [11, 1], '12': [12, 1],
                'barah': [12, 1], 'barvan': [12, 1], '13': [13, 1], 'terah': [13, 1], '14': [14, 1],
                'chaudah': [14, 1], '15': [15, 1], 'pandrah': [15, 1], '16': [16, 1], 'solah': [16, 1], '17': [17, 1],
                'satrah': [17, 1], '18': [18, 1], 'atharah': [18, 1], '19': [19, 1], 'unnish': [19, 1], '20': [20, 1],
                'bees': [20, 1], '21': [21, 1], 'ikkish': [21, 1], '22': [22, 1], 'baaish': [22, 1], '23': [23, 1],
                'teish': [23, 1], '24': [24, 1], 'chaubish': [24, 1], '25': [25, 1], 'pachhish': [25, 1],
                '26': [26, 1], 'chhabish': [26, 1], '27': [27, 1], 'sattaish': [27, 1], '28': [28, 1],
                'atthaish': [28, 1], '29': [29, 1], 'untish': [29, 1], '30': [30, 1], 'teesh': [30, 1],
                '31': [31, 1], 'ikattish': [31, 1]}

separators = {'se': 0, 'ke': 0, 'aur': 0, 'evam': 0, 'lekin': 0, 'par': 0, 'magar': 0, 'kintu': 0, 'parantu': 0,
              'ya': 0, 'kyunki': 0, 'isliye': 0}

TAG_PREV = 'prev'
TAG_NEXT = 'next'

HINDI_TAGGED_DATE = 'date'
HINDI_TAGGED_TIME = 'time'
