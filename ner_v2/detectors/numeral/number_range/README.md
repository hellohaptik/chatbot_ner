## Number Range Detector 

This detector module will help to detect minimum and maximum number values from text containing range values. For example - "200 to 300" (minimum=200 and maximum=300),  "more than 2000" (mininum=2000, maximum=Not define) 

 We are currently providing number detection supports in 6 languages, which are

- English
- Hindi

### Usage

- **Python Shell**

  ```python
  >> from ner_v2.detector.number.number_range.number_range_detection import NumberRangeDetector
  >> detector = NumberRangeDetector(entity_name='number_range', language='en')  # here language will be ISO 639-1 code
  >> detector.detect_entity(text= 'I annual salary is 200k-500k rupees')
  >> {'entity_value': [{'min_val': '200000', 'max_value': '500000', 'unit': 'rupees'}], 'original_text':['200k-500k rupees']}
  ```

- **Curl Command**

  ```bash
  # For a sample query with following parameters
  # message="i want more than 12 mangoes"
  # entity_name='number_range'
  # structured_value=None
  # fallback_value=None
  # bot_message=None
  # unit_type=None
  # source_language='en'
  # language_script='en'
  
  $ URL='localhost'
  $ PORT=8081
  
  $ curl -i 'http://'$URL':'$PORT'/v2/number_range?message=do%20hajaar%20char%20sau&entity_name=number&structured_value=&fallback_value=&bot_message=&source_language=en&language_script=en&unit_type='
  
  # Curl output
  $ {
      "data": [
          {
              "detection": "message",
              "original_text": "more than 12",
              "entity_value": {
                  "max_value": null,
                  "min_value": "12",
                  "unit": null
              },
              "language": "en"
          }
      ]
  }
  ```

  

### Steps to add new language for Number Range detection

In order to add any new language you have to follow below steps:

1. Create a directory with `ISO 639-1` code of that language inside `ner_v2/detectors/numeral/number_range/`.  

2. Create a directory named `data` inside language_code folder.

3. Add a CSV files named `number_range_keywords.csv` inside data folder.  

   Below is the folder structure of same after adding all the files for new language `xy`.

   ```python
   |__ner_v2
         |___detectors
             |___numeral
                 |___number_range
                     |___xy    # <- New language Added 
                     |	  |___data
                     |      |___number_range_keywords.csv
                     |      
                     |__number_detection.py 
   ```




####  GuideLines to create data files

Below is the brief about how to create data file `number_range_keywords.csv` All the description of the file is explained using hindi as a reference language. 

1. **number_range_keywords.csv**:  This files contains the vocabs for keywords which are present before or after or in between number values which defines whether the given is min or max value .

   |                        range_variants                        | position | range_type |
   | :----------------------------------------------------------: | :------: | :--------: |
   | k uper\| se upar\| se jada \| se adhik \| के ऊपर\|  से ज्यादा \|से जादा \| से अधिक |    1     |    max     |
   |                     kam se kam\| कम से कम                     |    -1    |    min     |
   | jyada se jyada \| lagbhag \| ज्यादा से ज्यादा \| जादा से जादा \| लगभग |    -1    |    max     |
   | se niche \| se kam \| se sasta \| se saste k aas paas\|  k aas pas\| k lagbhag \|  से नीचे \| से कम \| से सस्ता \| से सस्ते \|   के आस पास  \| के लगभग |    1     |    max     |
   |                           se\|-\|से                           |    0     |  min_max   |

   Here, 1st column will contain the number in their respective language script. 2nd column corresponds to numerals or name variants of number in respective language script and in english script.  

   3rd column contains the value representation of language number. 

   4th column define the whether the number is unit or scale. Units are individual numbers while scale are used with unit number to form numbers. Example - for number "200" , `2` is unit number and scale of  `100` is used to form a new number i.e `200`.    

2. **units.csv**:  This files contains the vocabs of units for number and their correspoding all variants possible .

   | unit_type | unit_value |                        unit_variants                         |
   | --------- | :--------: | :----------------------------------------------------------: |
   | currency  |   rupees   | rupees \| rupay \| paisa \| paise \| inr \| रूपीस \| रुपया \| रूपए\| पैसा\| पैसे\| ₹ |
   | currency  |   dollar   |                  Dollar \| usd \| डॉलर \| $                  |

   Here, the 1st column contains the type of unit (E.g. dollars, euros are "currency", centimetre, metre, kilometre are "distance"), 2nd column contains the value of unit which will be returned by number detector and 3rd column contains all the possible variants of that unit value (delimited by pipe `|`) for the language you are adding. (It is recommended to add Romanised versions of the variants you are adding)

#### Guidelines to add new detectors for number apart from builtin ones:

Create a new class `number_detection.py`  inside language directory.
To start with copy the code below

```python
import re
import os

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_DETECT_UNIT, NUMBER_DETECT_VALUE
from ner_v2.detectors.numeral.number.standard_number_detector import BaseNumberDetector


class NumberDetector(BaseNumberDetector):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name='number', unit_type=None):
        super(NumberDetector, self).__init__(entity_name=entity_name,
                                            
                                        data_directory_path=NumberDetector.data_directory_path,
                                             unit_type=unit_type)

```

Note that the class name must be `NumberDetector` 
and should inherit from `ner_v2.detectors.numeral.number.standard_number_detector.BaseNumberDetector`

Next we define a custom detector. For our purposes we will add a detector to detect text '2 people' and `2` as number and unit as `people`.

1. The custom detector must accept two arguments `number_list` and `original_list` and must operate on `self.processed_text`
2. The two arguments `number_list` and `original_list` can both be either None or lists of same length.
   `number_list` contains parsed number values and `original_list` contains their corresponding text substrings in the passed text that were detected as numbers.
3. Your detector must appened parsed number dicts with keys `'value', 'unit'` to `number_list`
   and to `original_list` their corresponding substrings from `self.processed_text` that were parsed into numbers.
4. Take care to not mutate `self.processed_text` in any way as main detect method in base class depends on it to eliminate already detected number from it after each detector is run.
5. Finally your detector must return a tuple of (number_list, original_list). Ensure that `number_list` and `original_list` are of equal lengths before returning them.

```python
    def _custom_detect_number_of_people_format(self, number_list=None, original_list=None):
        number_list = number_list or []
        original_list = original_list or []
        patterns = re.findall(r'\s((fo?r)*\s*([0-9]+)\s*(ppl|people|passengers?|travellers?|persons?|pax|adults?))\s',
                              self.processed_text.lower())
        for pattern in patterns:
            number_list.append({
                NUMBER_DETECT_VALUE: pattern[2],
                NUMBER_DETECT_UNIT: 'people'
            })
            original_list.append(pattern[0])

        return number_list, original_list
```

Once having defined a custom detector, we now add it to `self.detector_preferences` attribute. You can simply append your custom detectors at the end of this list or you can copy the default ordering from 
`detectors.numeral.number.standard_number_detector.BaseNumberDetector` and inject your own detectors in between.
Below we show an example where we put our custom detector on top to execute it before some builtin detectors.

```python
	def __init__(self, entity_name='number', unit_type=None):
        super(NumberDetector, self).__init__(entity_name=entity_name,
                                             data_directory_path=NumberDetector.data_directory_path,
                                            unit_type=unit_type)

        self.detector_preferences = [
            self._custom_detect_number_of_people_format,
            self._detect_number_from_digit,
            self._detect_number_from_numerals
        ]
```

Putting it all together, we have

```python
import re
import os

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_DETECT_UNIT, NUMBER_DETECT_VALUE
from ner_v2.detectors.numeral.number.standard_number_detector import BaseNumberDetector


class NumberDetector(BaseNumberDetector):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name='number', unit_type=None):
        super(NumberDetector, self).__init__(entity_name=entity_name,
                                             
                                             data_directory_path=NumberDetector.data_directory_path,
                                             unit_type=unit_type)


        self.detector_preferences = [
            self._custom_detect_number_of_people_format,
            self._detect_number_from_digit,
            self._detect_number_from_numerals
        ]

    def _custom_detect_number_of_people_format(self, number_list=None, original_list=None):
        number_list = number_list or []
        original_list = original_list or []
        patterns = re.findall(r'\s((fo?r)*\s*([0-9]+)\s*(ppl|people|passengers?|travellers?|persons?|pax|adults?))\s',
                              self.processed_text.lower())
        for pattern in patterns:
            number_list.append({
                NUMBER_DETECT_VALUE: pattern[2],
                NUMBER_DETECT_UNIT: 'people'
            })
            original_list.append(pattern[0])

        return number_list, original_list

```

For a working example, please refer `ner_v2/detectors/numerals/number/en/number_detection.py`

**Please note that the API right now is too rigid and we plan to change it to make it much more
easier to extend in the future**

