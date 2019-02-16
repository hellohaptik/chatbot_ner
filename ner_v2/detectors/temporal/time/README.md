## Time Detector 

This is the V2 version of time detector module that can detect and parse times in multiple languages from natural language text. Currently we provide supports for 6 languages, which are

- English
- Hindi
- Marathi
- Gujarati
- Telgu
- Tamil

### Usage

- **Python Shell**

  ```python
  >> from ner_v2.detector.temporal.time.time_detection import TimeDetector
  >> detector = TimeDetector(entity_name='time', language='hi')  # here language will be ISO 639-1 code
  >> detector.detect_entity(text= 'shaam ko sava 4 baje')
  >> {'entity_value': [{'hh':12 ,'mm': 10, 'nn': 'pm'}], 'original_text':['shaam ko sava 4 baje']}
  ```

- **Curl Command**

  ```bash
  message = "shaam sava 4 baje"
  entity_name = 'time'
  structured_value = None
  fallback_value = None
  bot_message = None
  timezone = 'UTC'  
  source_language = 'hi'
  language_script = 'en'

  $ URL='localhost'
  $ PORT=8081

  $ curl -i 'http://'$URL':'$PORT'/v2/time?message=shaam%20sava%204%20baje&entity_name=date&structured_value=&fallback_value=&bot_message=&source_language=hi&language_script=hi'

  # Curl output
  $ {
      "data": [
          {
              "detection": "message",
              "original_text": "shaam sava 4 baje",
              "entity_value": {
                  "mm": 15,
                  "hh": 4,
                  "nn": "pm"
              },
              "language": "hi"
          }
      ]
  }
  ```



### Steps to add new language for time detection

In order to add any new language you have to follow below steps:

1. Create a new folder with `ISO 639-1`  code of that language inside `ner_v2/detectors/temporal/time/`.  

2. Create a folder named `data` inside language_code folder.

3. Add three files named `time_constant.csv`, `numbers_constant.csv`, `datetime_diff_constant.csv` inside data folder. 

   Below is the folder structure of same after adding all the files for new language `xy`.

   ```python
   |__ner_v2/
     |__detectors/
       |__temporal/
         |__time/
           |__xy/    # <- New language Added
             |__init__.py
             |__data/
               |__time_constant.csv
               |__datetime_diff_constant.csv
               |__numbers_constant.csv
    
   ```




#### GuideLines to create data files

First, Create three data files `time_constant.csv`, `datetime_diff_constant.csv`, `numbers_constant.csv`.
Here, we explain the structure of each file using Hindi (hi) as a reference language.
You can examine these files at [ner_v2/detectors/temporal/time/hi/data/](hi/data)


1. **numbers_constant.csv**:  This files contains the vocabulary for numerals in desired langauge.
   For example, in hindi एक and दो  corresponds to number 1 and 2 respectively.
   For time, you would want to enter from 0 to 23 and any special cases.
   For example in Hindi time people use special words ढेड़ and ढाई for 1:30 and 2:30 respectively.

   |         key         | **numeric_respresentation** |
   | :-----------------: | :-------------------------: |
   |     १\|एक \|ek      |              1              |
   |     २\|दो \| do     |              2              |
   | २१ \|इक्कीस\| ikkis |             21              |

   **1st column will contain the variations speakers use while writing that number in the target language script**.It is recommended to add Romanised (transliterated) variations as well.

   **2nd column corresponds to their actual numerical representation**. It must strictly contain an int or float.

   For reference see [numbers_constant.csv](hi/data/numbers_constant.csv) file for Hindi


2. **time_constant.csv**: This file contains the words that occurs only when referencing time like
   `बजे`, `घंटे` (hours),  `मिनट` (minutes), `सुबह` (morning) etc.

   |                   key                    |    time_type     | meridiem |
   | :--------------------------------------: | :--------------: | :------: |
   |                अभी\|abhi                 |  relative_time   |    NA    |
   |              तुरंत\|turant               |  relative_time   |    NA    |
   | बजे\|बजकर\|बज\|baje\|bajkr\|bajkar\|bje\|baj |       hour       |    NA    |
   | घंटा\|घंटे\|घंटों\|ghanta\|ghante\|ghanton |       hour       |    NA    |
   | मिनट\|मिनटों\|minton\|minutes\|mins\|minute\|min |      minute      |    NA    |
   |            सुबह\|subah\|subeh            | daytime_meridiem |    am    |
   |                रात\|raat                 | daytime_meridiem |    pm    |

   **1st column will contain word variations which are used in conjunction with numbers to specify a time.**As you can see in the above table contains words like `घंटे` (hour), `मिनट` (minute), `सुबह` (morning), `रात` (night)

   **2nd column defines how a mention of a variant from the first column modifies the mentioned time.**Below is a description of all possible values for the column

   - `relative_time`:  phrases that indicate mentioned time is relative to current time.
   - `hour`:  phrases are used to indicate hours (E.g. 5 "hours" 30 minutes 50 seconds, 5 "bajkar" 3 minute)
   - `minute`: phrases are used to indicate minutes (E.g. 5 hours 30 "minutes", 5 bajkar 3 "minute")
   - `second`:  phrases are used to indicate seconds (E.g. 5 hours 30 minutes 50 "seconds")
   - `daytime_meridiem`: phrases that can decide the meridiem of 12 hour format time (E.g. morning -> am, noon -> pm, night -> pm)

   **3rd column defines explicitly what meridiem to use when a variant from 1st column is present in the message.**Values can either be `am` (when something like "morning" is mentioned), `pm` (when something like "night" is mentioned),
   or `NA` when both or none are applicable and it is upto the detector to infer 

   For reference see [time_constant.csv](hi/data/time_constant.csv) file for Hindi

3. **datetime_diff_constant.csv**: This file contains the vocabulary which is used while referencing for both date and time.
   This vocabulary is used to mention dates and time in past or future w.r.t current time or to add a delta (of hours/minutes) in mentioned time.
   Some examples are **पिछले** दिन (previous day), **पिछले** घंटे (previous hour)

   |           key            | present_in_start | adding_magnitude |   datetime_type   |
   | :----------------------: | :--------------: | :--------------: | :---------------: |
   |       बाद \| baad        |      False       |        1         | add_diff_datetime |
   |    इस \|  इसी \| isi     |       True       |        0         | add_diff_datetime |
   | पिछले \| पिछला\| pichhla |       True       |        -1        | add_diff_datetime |
   |   सावा \| sava \| sawa   |       True       |       0.25       |   ref_datetime    |
   |      पौने \| paune       |       True       |      -0.25       |   ref_datetime    |

   Here, **1st column contains phrases which can be used to mention a relative delta for hour in time**
        - "after" one hour
        - "this" hour
        - "last" hour
        - three hours "later"
        - "quarter to" 5
        - ek ghante "baad" # one hour later
        - "sava" teen # 15 minutes past 3
        - "paune" paanch # "quarter to" 5

   **2nd column mentions if the entries in the first column appear as a prefix to the time mention**. The value must be a boolean (either True or False). For example, in the sentence `3 ghante baad `(3 hours later) ,  "baad" (later) is written as a suffix to "3 ghante" (3 hours), hence its `present_in_start` will be False.

   **3rd column contains the relative number of hours to add to referenced time**, (1 for adding an hour, -1 for subtracting an hour). Here you can also add things like "quarter to N" with adding_magnitude -0.25 which indicates to the parse to remove 0.25 hour = 15 minutes before N i.e. return the time 15 minutes before N.

    **4th column defines the delta type.** Below are supported values

   1. `add_diff_datetime`:  If phrases in the first column appear as suffix to the time mention and modifies the time by adding the defined number of hours in the third column
   2. `ref_datetime`: If phrases in the first column appear as prefix to the time mention and modifies the time by adding the defined number of hours in the third column

   For reference see [datetime_diff_constant.csv](hi/data/datetime_diff_constant.csv) file for Hindi
