## Date Detector 

This is the V2 version of date detector module that will detect date in multiple languages from natural language text containing date entity. Currently we provide supports for 6 languages, which are

- English
- Hindi
- Marathi
- Gujarati
- Telugu
- Tamil

### Usage

- **Python Shell**

  ```python
  >> from ner_v2.detectors.temporal.date.date_detection import DateDetector
  >> detector = DateDetector(entity_name='date', language='hi')  # here language will be ISO 639-1 code
  >> detector.detect_entity(text= 'agla mangalvar')
  >> {'entity_value': [{'dd':12 ,'mm': 10, 'yy': 2018}], 'original_text':['agla mangalvar']}
  ```

- **Curl Command**

  ```bash
  # For a sample query with following parameters
  # message="agle mahine ka doosra somvar"
  # entity_name='date'
  # structured_value=None
  # fallback_value=None
  # bot_message=None
  # timezone='UTC'
  # source_language='hi'
  # language_script='en'
  
  $ URL='localhost'
  $ PORT=8081
  
  $ curl -i 'http://'$URL':'$PORT'/v2/date?message=agle%20mahine%20ka%20doosra%20somvar&entity_name=date&structured_value=&fallback_value=&bot_message=&source_language=hi&language_script=hi'
  
  # Curl output
  $ {
      "data": [
          {
              "detection": "message",
              "original_text": "agle mahine ka doosra somvar",
              "entity_value": {
                  "end_range": false,
                  "from": false,
                  "normal": true,
                  "value": {
                      "mm": 11,
                      "yy": 2018,
                      "dd": 12,
                      "type": "date"
                  },
                  "to": false,
                  "start_range": false
              },
              "language": "hi"
          }
      ]
  }
  ```

  

### Steps to add new language for date detection

In order to add any new language you have to follow below steps:

1. Create a new folder with `ISO 639-1`  code of that language inside `ner_v2/detectors/temporal/date/`.  

2. Create a folder named `data` inside language_code folder.

3. Add three files named `date_constant.csv`, `numbers_constant.csv`, `datetime_diff_constant.csv`inside data folder.  

   Below is the folder structure of same after adding all the files for new language `xy`.

   ```python
   |__ner_v2
         |___detectors
             |___temporal
                 |___date
                     |___xy    # <- New language Added 
                     |	  |___data
                     |      |___date_constant.csv
                     |      |___datetime_diff_constant.csv
                     |      |___numbers_constant.csv
                     |
                     |__date_detection.py 
   ```




####  GuideLines to create data files

Below is the brief about how to create three data files `date_constant.csv`, `datetime_diff_constant.csv`, `numbers_constant.csv`.  All the description of each file is explained using hindi as a reference language. 

1. **numbers_constant.csv**:  This files contains the vocabs for numerals in local langauge like in hindi एक,  दो  corresponds to number 1 and 2 respectively.

   |        key         | **numeric_respresentation** |
   | :----------------: | :-------------------------: |
   |     १\|एक \|ek     |              1              |
   |    २\|दो \| do     |              2              |
   | २१ \|इक्कीस\| ikkis |             21              |

   Here, 1st column will contain the numerical value in the local language script plus in english script, Second column corresponds to their actual numerical representation.

   For reference see `number_constant` file for hindi - https://github.com/hellohaptik/chatbot_ner/blob/language_datetime_code_review/ner_v2/detectors/temporal/date/hi/data/numbers_constant

    

2. **date_constant.csv**: This file contains the vocab that occurs only in reference for date entity like  आज,  कल,  तारिक,  सोमवार  etc.

   |               key                | **numeric_representation** | **date_type**  |
   | :------------------------------: | :------------------------: | :------------: |
   |            आज \| aaj             |             0              | relative_date  |
   |        रविवार \| ravivar         |             6              |    weekday     |
   |        दिसंबर \| december         |             12             |     month      |
   |     महीना \| महीने \| mahine      |             NA             | month_literal  |
   | तारिक \| तारिख \| tarikh\| tarik |             NA             | month_date_ref |
   |       दिन\|दिनों\|din\|dino       |             NA             |  date_literal  |

   Here, 1st column will contain the vocabs which is used to detect date entity, 2nd column will have numerical_representation. For example आज  will corresponds to 0 day difference from reference date. रविवार will be corresponding to 6th day of week, दिसंबर corresponds to 12th month of year, word like महीना and तारिक  don’t have any numerical representation hence there numerical value will be NA.  3rd column define the category of word. There are four different date_type categories, below are their detailed description.

   1. ***relative_datedate***:  date which is derived with reference to current date.
   2. ***day_literal***:  Words literally spoken for days like दिन,  दिवस.
   3. ***month_literal***: Words literally spoken for months like महीना, मास, महीने.
   4. **weekday**:  Words which represent weekday like सोमवार, मंगलवार.
   5. ***month***: Words which represent month like जनवरी, फरवरी.
   6. ***month_date_ref***: Words which present some day of month like 2 *तारिक*.

   For reference see `date_constant.csv` file for hindi - https://github.com/hellohaptik/chatbot_ner/blob/language_datetime_code_review/ner_v2/detectors/temporal/date/hi/data/date_constant.csv

   

3. **datetime_diff_constant.csv**:  This file contains the vocabs which come in reference for both date and time entity. These vocabs help to reference to some datetime in past and future w.r.t current time or create diff in mentioned time. Examples are  **पिछले** दिन,  **पिछले** घंटे

   |           key           | present_in_start | adding_magnitude |   datetime_type   |
   | :---------------------: | :--------------: | :--------------: | :---------------: |
   |       बाद \| baad       |      False       |        1         | add_diff_datetime |
   |    इस \|  इसी \| isi    |       True       |        0         | add_diff_datetime |
   | पिछले \| पिछला\| pichhla |       True       |        -1        | add_diff_datetime |
   |  सावा \| sava \| sawa   |       True       |       0.25       |   ref_datetime    |
   |      पौने \| paune       |       True       |      -0.25       |   ref_datetime    |

   Here, 1st column contains the word which can in reference for date time, 2nd column define the positioning of this word in entity whether it comes in start or in end. For example, in sentence *2 din baad* ,  "baad" came after "2 din"(date entity), hence its present_in_start will be false.  3rd column define the magnitude it is adding to referenced date or time, (1 if its adding positively, -1 if adding negatively). 4th column define the datetime type. Below are their detailed description.

   1. ***add_diff_datetime***:  Words which are referencing to datetime difference from current time like word baad in 2  दिन *बाद*  referring to a day, which comes 2 day later from current date.

   2. **ref_datetime**: Words which referenced to create difference in time reference next to it. Example- सावा 4 , here whole sentence is referring to time 4:15.

      

      For reference see `datetime_diff_constant.csv` file for hindi - https://github.com/hellohaptik/chatbot_ner/blob/language_datetime_code_review/ner_v2/detectors/temporal/date/hi/data/datetime_diff_constant.csv



#### Guidelines to add new detectors for date apart from builtin ones:

Create a new class `date_detection.py`  inside language directory.
To start with copy the code below

```python
import re
import os

from ner_v2.constant import TYPE_EXACT
from ner_v2.detectors.temporal.date.standard_date_regex import BaseRegexDate
from ner_v2.constant import LANGUAGE_DATA_DIRECTORY

class DateDetector(BaseRegexDate):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)
    def __init__(self, entity_name, timezone='UTC', past_date_referenced=False):
        super(DateDetector, self).__init__(entity_name,
                                           data_directory_path=DateDetector.data_directory_path,
                                           timezone=timezone,
                                           past_date_referenced=past_date_referenced)
```

Note that the class name must be `DateDetector` 
and should inherit from `ner_v2.detectors.temporal.date.standard_date_regex.BaseRegexDate`

Next we define a custom detector. For our purposes we will add a deector to detect 'christmas' and return 25th Dec.

1. The custom detector must accept two arguments `date_list` and `original_list` and must operate on `self.processed_text`
2. The two arguments `date_list` and `original_list` can both be either None or lists of same length.
   `date_list` contains parsed date values and `original_list` contains their corresponding text substrings
   in the passed text that were detected as dates.
3. Your detector must appened parsed date dicts with keys `'dd', 'mm', 'yy', 'type'` to `date_list`
   and to `original_list` their corresponding substrings from `self.processed_text` that were parsed into dates.
4. Take care to not mutate `self.processed_text` in any way as main detect method in base class depends on it
   to eliminate already detected dates from it after each detector is run.
5. Finally your detector must return a tuple of (date_list, original_list). Ensure that `date_list` and `original_list`
   are of equal lengths before returning them.

Types of dates that go under `'type'` key are defined at `ner_v2/constant.py`

```python
    def custom_christmas_date_detector(self, date_list=None, original_list=None):
            date_list = date_list or []
            original_list = original_list or []
    
            christmas_regex = re.compile(r'((christmas|xmas|x-mas|chistmas))')
            day_match = christmas_regex.findall(self.processed_text)
            for match in day_match:
                original = match[0]
                date = {
                    'dd': 25,
                    'mm': 12,
                    'yy': self.now_date.year,
                    'type': TYPE_EXACT
                }
                date_list.append(date)
                original_list.append(original)
            return date_list, original_list
```

Once having defined a custom detector, we now add it to `self.detector_preferences` attribute. You can simply
append your custom detectors at the end of this list or you can copy the default ordering from 
`detectors.temporal.date.standard_date_regex.BaseRegexDate` and inject your own detectors in between.
Below we show an example where we put our custom detector in middle to execute it before some builtin detectors.

```python
    def __init__(self, entity_name, timezone='UTC', past_date_referenced=False):
            super(DateDetector, self).__init__(entity_name,
                                               data_directory_path=DateDetector.data_directory_path,
                                               timezone=timezone,
                                               past_date_referenced=past_date_referenced)
            self.detector_preferences = [
                self._detect_relative_date,
                self._detect_date_month,
                self._detect_date_ref_month_1,
                self._detect_date_ref_month_2,
                self._detect_date_ref_month_3,
                self.custom_christmas_date_detector,
                self._detect_date_diff,
                self._detect_after_days,
                self._detect_weekday_ref_month_1,
                self._detect_weekday_ref_month_2,
                self._detect_weekday_diff,
                self._detect_weekday
            ]

```

Putting it all together, we have

```python
import re
import os

from ner_v2.constant import TYPE_EXACT
from ner_v2.detectors.temporal.date.date_detection import get_lang_data_path
from ner_v2.detectors.temporal.date.standard_date_regex import BaseRegexDate


class DateDetector(BaseRegexDate):
    data_directory_path = get_lang_data_path(os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep))

    def __init__(self, entity_name, timezone='UTC', past_date_referenced=False):
        super(DateDetector, self).__init__(entity_name,
                                           data_directory_path=DateDetector.data_directory_path,
                                           timezone=timezone,
                                           past_date_referenced=past_date_referenced)
        self.detector_preferences = [
            self._detect_relative_date,
            self._detect_date_month,
            self._detect_date_ref_month_1,
            self._detect_date_ref_month_2,
            self._detect_date_ref_month_3,
            self.custom_christmas_date_detector,
            self._detect_date_diff,
            self._detect_after_days,
            self._detect_weekday_ref_month_1,
            self._detect_weekday_ref_month_2,
            self._detect_weekday_diff,
            self._detect_weekday
        ]

    def custom_christmas_date_detector(self, date_list=None, original_list=None):
        date_list = date_list or []
        original_list = original_list or []

        chritmas_regex = re.compile(r'((christmas|xmas|x-mas|chistmas))')
        day_match = chritmas_regex.findall(self.processed_text)
        for match in day_match:
            original = match[0]
            date = {
                'dd': 25,
                'mm': 12,
                'yy': self.now_date.year,
                'type': TYPE_EXACT
            }
            date_list.append(date)
            original_list.append(original)
        return date_list, original_list
```

For a working example, please refer `ner_v2/detectors/temporal/date/hi/date_detection.py`

**Please note that the API right now is too rigid and we plan to change it to make it much more
easier to extend in the future**

