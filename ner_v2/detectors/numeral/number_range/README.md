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

2. Create a directory named `data` inside the language_code folder.

3. Add a CSV file named `number_range_keywords.csv` inside data folder.  

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

Below is the brief about how to create data file `number_range_keywords.csv` All the description of the file is explained using Hindi as a reference language. 

1. **number_range_keywords.csv**:  This file contains the vocabs for range keywords, their position around number values and their range type.

   |                        range_variants                        | position | range_type |
   | :----------------------------------------------------------: | :------: | :--------: |
   | k uper\| se upar\| se jada \| se adhik \| के ऊपर\|  से ज्यादा \|से जादा \| से अधिक |    1     |    min     |
   |                     kam se kam\| कम से कम                     |    -1    |    min     |
   | jyada se jyada \| lagbhag \| ज्यादा से ज्यादा \| जादा से जादा \| लगभग |    -1    |    max     |
   | se niche \| se kam \| se sasta \| se saste k aas paas\|  k aas pas\| k lagbhag \|  से नीचे \| से कम \| से सस्ता \| से सस्ते \|   के आस पास  \| के लगभग |    1     |    max     |
   |                           se\|-\|से                           |    0     |  min_max   |

   Here, the 1st column will contain the variants of range keywords separated by pipes, which are present before or after or in between number values and defines what type of number value is present, either min or max. 

   2rd column corresponds to the position of the keyword. If 1 means it will be present after number value, -1 if present before number.  

   3rd column defines the range type of number i.e if it contains min value or max value or both.    

   **For example** - *mujhe 2000 se jada log chahiye kal ki rally me* . In this text, range keyword `se jada` which is present in position `1` (after number) defines that number `2000` is the minimum value defined in the text, since no maximum value specified in text, hence it will be null.


#### Guidelines to add new detectors for number range apart from builtin ones:

Create a new class `number_range_detection.py`  inside language directory.
To start with copy the code below

```python
import re
import os

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_REPLACE_TEXT
from ner_v2.detectors.numeral.number_range.standard_number_range_detector import BaseNumberRangeDetector


class NumberRangeDetector(BaseNumberRangeDetector):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name, language, unit_type=None):
        super(NumberRangeDetector, self).__init__(entity_name=entity_name,
                                                  language=language,
                                                  data_directory_path=NumberRangeDetector.data_directory_path,
                                                  unit_type=unit_type)
```

Note that the class name must be `NumberRangeDetector` 
and should inherit from `ner_v2.detectors.numeral.number_range.standard_number_range_detector.BaseNumberRangeDetector`

Next, we define a custom detector. For our purposes, we will add a detector to detect number range from text of patter 'between *number1* and *number2*. It will detect number1 and number2 as minimum value and maximum value respectively.

1. The custom detector must accept two arguments `number_range_list` and `original_list` and must operate on `self.processed_text (This text contained tagged number text i.e number will be replaced with __dnumber__<number>`). So in your pattern, you just have to include pattern with number tag instead of `\d+` for the number. (as it handle all number having decimal, ordinal and integer)
2. The two arguments `number_range_list` and `original_list` can both be either None or lists of the same length.
   `number_range_list` contains parsed min and max value  along with unit and `original_list` contains their corresponding text substrings in the passed text that were detected as numbers range.
3. Your detector must append parsed number range dicts with keys `'min_value', 'max_value', 'unit'` to `number_range_list`
   and to `original_list` their corresponding substrings from `self.processed_text` that were parsed into numbers.
4. Take care to not mutate `self.processed_text` in any way as main detect method in base class depends on it to eliminate already detected number from it after each detector is run.
5. Finally, your detector must return a tuple of (number_range_list, original_list). Ensure that `number_range_list` and `original_list` are of equal lengths before returning them.

```python

    def _custom_num_range_between_num_and_num(self, number_range_list=None, original_list=None):
        number_range_list = number_range_list or []
        original_list = original_list or []
        between_range_pattern = re.compile(ur'(between\s+({number}\d+)(?:\s+and|-)'
                                           ur'\s+({number}\d+))'.format(number=NUMBER_REPLACE_TEXT), re.UNICODE)
        number_range_matches = between_range_pattern.findall(self.processed_text)
        for match in number_range_matches:
            number_range, original_text = self._get_number_range(min_part_match=match[1], max_part_match=match[2],
                                                                 full_match=match[0])
            if number_range and original_text:
                number_range_list.append(number_range)
                original_list.append(original_text)

        return number_range_list, original_list

```

Once having defined a custom detector, we now add it to `self.detector_preferences` attribute. You can simply append your custom detectors at the end of this list or you can copy the default order from 
`detectors.numeral.number_range.standard_number_range_detector.BaseNumberRangeDetector` and inject your own detectors in between.
Below we show an example where we put our custom detector on top to execute it before some builtin detectors.

```python
    def __init__(self, entity_name, language, unit_type=None):
        super(NumberRangeDetector, self).__init__(entity_name=entity_name,
                                                  language=language,
                                                  data_directory_path=NumberRangeDetector.data_directory_path,
                                                  unit_type=unit_type)

        self.detector_preferences = [self._detect_min_max_num_range,
                                     self._custom_num_range_between_num_and_num,
                                     self._detect_min_num_range_with_prefix_variants,
                                     self._detect_min_num_range_with_suffix_variants,
                                     self._detect_max_num_range_with_prefix_variants,
                                     self._detect_max_num_range_with_suffix_variants
                                     ]
```

Putting it all together, we have

```python
import re
import os

from ner_v2.constant import LANGUAGE_DATA_DIRECTORY
from ner_v2.detectors.numeral.constant import NUMBER_REPLACE_TEXT
from ner_v2.detectors.numeral.number_range.standard_number_range_detector import BaseNumberRangeDetector


class NumberRangeDetector(BaseNumberRangeDetector):
    data_directory_path = os.path.join((os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep)),
                                       LANGUAGE_DATA_DIRECTORY)

    def __init__(self, entity_name, language, unit_type=None):
        super(NumberRangeDetector, self).__init__(entity_name=entity_name,
                                                  language=language,
                                                  data_directory_path=NumberRangeDetector.data_directory_path,
                                                  unit_type=unit_type)

        self.detector_preferences = [self._detect_min_max_num_range,
                                     self._custom_num_range_between_num_and_num,
                                     self._detect_min_num_range_with_prefix_variants,
                                     self._detect_min_num_range_with_suffix_variants,
                                     self._detect_max_num_range_with_prefix_variants,
                                     self._detect_max_num_range_with_suffix_variants
                                     ]

    def _custom_num_range_between_num_and_num(self, number_range_list=None, original_list=None):
        """Detects number range of text of pattern between number1 to number2
        This is a custom created patterns which will be called after all the standard detector will ran.

        Returns:
            A tuple of two lists with first list containing the detected number ranges and second list
            containing their corresponding substrings in the original message.

            For example:
                input text: "my salary range is between 2000 to 3000"
                output: ([{'min_value': '2000', 'max_value': '3000', 'unit': None}], ['between 2000 to 3000'])

        """
        number_range_list = number_range_list or []
        original_list = original_list or []
        between_range_pattern = re.compile(ur'(between\s+({number}\d+)(?:\s+and|-)'
                                           ur'\s+({number}\d+))'.format(number=NUMBER_REPLACE_TEXT), re.UNICODE)
        number_range_matches = between_range_pattern.findall(self.processed_text)
        for match in number_range_matches:
            number_range, original_text = self._get_number_range(min_part_match=match[1], max_part_match=match[2],
                                                                 full_match=match[0])
            if number_range and original_text:
                number_range_list.append(number_range)
                original_list.append(original_text)

        return number_range_list, original_list
```

For a working example, please refer `ner_v2/detectors/numerals/number_range/en/number_range_detection.py`

**Please note that the API right now is too rigid and we plan to change it to make it much more
easier to extend in the future**

