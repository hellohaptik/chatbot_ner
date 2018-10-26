## Time Detector 

This is the V2 version of time detector module that will detect time in multiple languages from raw text containing time entity. Currently we provide supports for 6 languages, which are

- English
- Hindi
- Marathi
- Gujarati
- Telgu
- Tamil

### Usage

```python
>> from ner_v2.detector.temporal.time.time_detection import TimeDetector
>> detector = TimeDetector(entity_name='time', language='hi')  # here language will be ISO 639-1 code
>> detector.detect_entity(text= 'shaam ko sava 4 baje')
>> {'entity_value': [{'hh':12 ,'mm': 10, 'nn': 'pm'}], 'original_text':['shaam ko sava 4 baje']}
```



### Steps to add new language for time detection

In order to add any new language you have to follow below steps:

1. Create a new folder with `ISO 639-1`  code of that language inside `ner_v2/temporal/detector/time/`.  

2. Create a folder named `data` inside language_code folder.

3.  Add three files named `time_constant.csv`, `numbers_constant.csv`, `datetime_diff_constant.csv` inside data folder. Data these files will have is discussed later.

4. Create a file `time_detection.py ` inside language_code folder and put below code inside that file.

   ```python
   from ner_v2.detectors.temporal.constant import LANGUAGE_DATA_DIRECTORY
   from ner_v2.detectors.temporal.time.standard_time_regex import BaseRegexTime
   
   import os
   
   
   class TimeDetector(BaseRegexTime):
       def __init__(self, entity_name, timezone='UTC'):
           data_directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)).rstrip(os.sep),
                                              LANGUAGE_DATA_DIRECTORY)
   
           super(TimeDetector, self).__init__(entity_name=entity_name, timezone=timezone,
                                              data_directory_path=data_directory_path)
   
       def detect_time(self, text):
           """
           Detects exact time for complete time information - hour, minute, time_type available in text
   
           Returns:
               A tuple of two lists with first list containing the detected time entities and second list containing their
               corresponding substrings in the given text.
           """
   
           self.text = text
           self.processed_text = self.text
           self.tagged_text = self.text
   
           time_list, original_text_list = self._detect_time_from_standard_regex()
   
           return time_list, original_text_list
   ```

    

   Below is the folder structure of same after adding all the files for new language `xy`.

   ```python
   --ner_v2
     |___detector
         |___temporal
             |___time
                 |___xy    # <- New language Added 
                 |	  |___data
                 |   |   |___time_constant.csv
                 |   |   |___datetime_diff_constant.csv
                 |   |   |___numbers_constant.csv
                 |   |
                 |	  |___time_detection.py
                 |
                 |__time_detection.py 
   ```



#### GuideLines to create data files

Below is the brief about how to create three data files `time_constant.csv`, `datetime_diff_constant.csv`, `numbers_constant.csv`.  All the description of each file is explained using hindi as a reference language. 

1. **numbers_constant.csv**:  This files contains the vocabs for numerals in local langauge like in hindi एक,  दो  corresponds to number 1 and 2 respectively.

   |        key         | **numeric_respresentation** |
   | :----------------: | :-------------------------: |
   |     १\|एक \|ek     |              1              |
   |    २\|दो \| do     |              2              |
   | २१ \|इक्कीस\| ikkis |             21              |

   Here, 1st column will contain the numerical value in the local language script plus in english script, Second column corresponds to their actual numerical representation.

   For reference see `number_constant` file for hindi - https://github.com/hellohaptik/chatbot_ner/blob/language_datetime_code_review/ner_v2/detectors/temporal/time/hi/data/numbers_constant

    

2. **time_constant.csv**: This file contains the words that occurs only in reference to time entity like  बजे,  घंटे,  मिनट,  सुबह  etc.

   |                       key                       |    time_type    | meridian |
   | :---------------------------------------------: | :-------------: | :------: |
   |                    अभी\|abhi                    |  relative_time  |    NA    |
   |                   तुरंत\|turant                   |  relative_time  |    NA    |
   |   बजे\|बजकर\|बज\|baje\|bajkr\|bajkar\|bje\|baj   |      hour       |    NA    |
   |      घंटा\|घंटे\|घंटों\|ghanta\|ghante\|ghanton      |      hour       |    NA    |
   | मिनट\|मिनटों\|minton\|minutes\|mins\|minute\|min |     minute      |    NA    |
   |                सुबह\|subah\|subeh                | daytime_merdian |    am    |
   |                    रात\|raat                    | daytime_merdian |    pm    |

   Here, 1st column will contain word which is used to detect time entity, 3rd column define meridian based on time_key, will be NA where time_key occur for both instances (am and pm). 2nd column define the time type, below is the description of each time type.

   1. ***relative_time***:  time which is derived with reference to current time.

   2. ***hour***:  Words which represent hours in time entity.

   3. ***minute***: Words which represent minutes in time in entity.

   4. ***second***:  Words which represent seconds in time in entity.

   5. ***daytime_merdian***: Words which represent day time reference or meridian in support of time entity. For ex. 'subah me 2 baje' -> here it define what meridian to consider for 2 baje i.e am

      

   For reference see `date_constant.csv` file for hindi - https://github.com/hellohaptik/chatbot_ner/blob/language_datetime_code_review/ner_v2/detectors/temporal/time/hi/data/time_constant.csv

   

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

For reference see `datetime constant_csv` file for hindi - https://github.com/hellohaptik/chatbot_ner/blob/language_datetime_code_review/ner_v2/detectors/temporal/date/hi/time/datetime_diff_constant.csv



