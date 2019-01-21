## API Documentation

### List of Entity Types
-  [Text Entity](#1-text-entity)
- [Phone number](#2-phone-number)
- [Email](#3-email)
- [City Name](#4-city-name)
- [PNR Number](#5-pnr-number)
- [Number Entity](#6-number-entity)
- [Time Entity](#7-time-entity)
- [Time with range](#8-time-with-range)
- [Date Entity](#9-date-entity)
- [Budget](#10-budget)
- [Apparel's Shopping Size](#11-apparels-shopping-size)
- [Passenger Count](#12-passenger-count)
- [Location Entity](#13-location-entity)
- [Person Name](#14-person-name)
- [Regex Entity](#15-regex-entity)

### Tag multiple entities
[Data Tagging](#data-tagging)



Following are the list of different entity types along with its API call:

### 1. Text Entity

> entity_type: text

The Text Detector has the capability to detect custom text entity within the given text.  The detector has the ability to handle multilanguage text.

**API Examples:**

- **Example 1: *Detecting text entity from message***

  - *Python:* 
    ```python
    >>> message='i want to order chinese from  mainland china and pizza from domminos'
    >>> entity_name='restaurant'
    >>> structured_value=None
    >>> fallback_value=None
    >>> bot_message=None
    >>> source_language='en'
    
    >>> from ner_v1.chatbot.entity_detection import get_text
    >>> output = get_text(message=message, entity_name=entity_name,
                          structured_value=structured_value,
                          fallback_value=fallback_value,
                          bot_message=bot_message,language=source_language)
    >>> print(output)
    ```
    The above can also be done from within the Docker container's shell. Setup is in docker.md file.

  - *CURL command:*
    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/text/?message=i%20want%20to%20order%20chinese%20from%20%20mainland%20china%20and%20pizza%20from%20domminos&entity_name=restaurant&structured_value=&fallback_value=None&bot_message=&source_language=en'
    ```

    > **Output **:

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "mainland china",
          "entity_value": {
            "value": "Mainland China"
          },
            "language": "en"
        },
        {
          "detection": "message",
          "original_text": "dominos",
          "entity_value": {
            "value": "Domino's Pizza"
          },
            "language": "en"
        }
      ]
    }
    ```




- **Example 2: *Detecting text entity from structured value***

  - *Python:* 

    ```python
    >>> message = 'i wanted to watch movie'
    >>> entity_name = 'movie'
    >>> structured_value = 'inferno'
    >>> fallback_value = None
    >>> bot_message = None
    >>> source_langauge='en'
    
    >>> from ner_v1.chatbot.entity_detection import get_text
    >>> output = get_text(message=message, entity_name=entity_name,
        	              structured_value=structured_value,
            	          fallback_value=fallback_value,
                	      bot_message=bot_message,langauge=source_language)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/text/?message=i%20wanted%20to%20watch%20movie&entity_name=movie&structured_value=inferno&fallback_value=None&bot_message=&source_language=en'
    ```
    > **Output **:

    ```json
    {
      "data": [
        {
          "detection": "structure_value_verified",
          "original_text": "inferno",
          "entity_value": {
            "value": "Inferno"
          },
            "language":"en"
        }
      ]
    }
    ```





### 2. Phone number

> entity_type: phone_number

The Phone Number Detector has the capability to detect phone numbers from within the given text. The detector has the ability to handle multilanguage text. Additionally, this detector is scaled to handle domestic as well as international phone numbers.  

*This module has been updated to v2 version of chatbot_ner.*

**API Examples:**

- **Example 1: *Detecting phone number from message***

  - *Python:* 

    ```python
    >>> message = u'send a message on 91 9820334455'
    >>> entity_name = 'phone_number'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> source_langauge='en'       # here language will be ISO 639-1 code
    
    >>> from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector      
    >>> detector = PhoneDetector(language=source_langauge,
                                 entity_name=entity_name) 
    >>> output = detector.detect(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value,
                                 bot_message=bot_message,language=source_language)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/phone_number/?message=my%20contact%20number%20is%209049961794&entity_name=phone_number&structured_value=&fallback_value=None&bot_message=&source_language=en'
    ```
    > **Output **:

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "9049961794",
          "entity_value": {
            "value": "9049961794"
          },
        "language": "en"
        }
      ]
    }
    ```

- **Example 2:  *Detecting phone number from fallback value***

  - *Python:* 

    ```python
    >>> message = 'Please call me'
    >>> entity_name = 'phone_number'
    >>> structured_value = None
    >>> fallback_value = '9049961794'
    >>> bot_message = None
    >>> source_langauge='en'
    
    >>> from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector      
    >>> detector = PhoneDetector(language=source_langauge,
                                 entity_name=entity_name) 
    >>> output = detector.detect(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value,
                                 bot_message=bot_message,language=source_language)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/phone_number/?message=Please%20call%20me&entity_name=phone_number&structured_value=&fallback_value=9049961794&bot_message=&source_language=en'
    ```
    > **Output **:

    ```json
    {
      "data": [
        {
          "detection": "fallback_value",
          "original_text": "9049961794",
          "entity_value": {
            "value": "9049961794"
          },
            "language": "en"
        }
      ]
    }
    ```



### 3. Email

> entity_type: email

The Email Detector has the capability to detect emails within the given text. 

**API Example:**

- **Example 1:  *Detecting emails from message***

  - *Python:*

    ```python
    >>> message = 'my email id is amans.rlx@gmail.com'
    >>> entity_name = 'email'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    
    >>> from ner_v1.chatbot.entity_detection import get_email
    >>> output = get_email(message=message,entity_name=entity_name,
                           structured_value=structured_value,
                           fallback_value=fallback_value, bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/email/?message=my%20email%20id%20is%20amans.rlx%40gmail.com&entity_name=email&structured_value=&fallback_value=&bot_message='
    ```
    > **Output **

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "amans.rlx@gmail.com",
          "entity_value": {
            "value": "amans.rlx@gmail.com"
          }
        }
      ]
    }
    ```

- ***Example 2:  Detecting email from fallback value***

  - *Python:*

    ```python
    >>> message = 'send this me to my email'
    >>> entity_name = 'email'
    >>> structured_value = None
    >>> fallback_value = 'amans.rlx@gmail.com'
    >>> bot_message = None
    
    >>> from ner_v1.chatbot.entity_detection import get_email
    >>> output = get_email(message=message,entity_name=entity_name,
                           structured_value=structured_value,
                           fallback_value=fallback_value, bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/email/?message=send%20me%20to%20my%20email&entity_name=email&structured_value=&fallback_value=amans.rlx@gmail.com&bot_message='
    ```
    > **Output **

    ```json
    {
      "data": [
        {
          "detection": "fallback_value",
          "original_text": "amans.rlx@gmail.com",
          "entity_value": {
            "value": "amans.rlx@gmail.com"
          }
        }
      ]
    }
    ```



### 4. City Name

> entity_type: city

The City  Detector has the capability to detect city name within the given text.  The detector has the ability to handle multilanguage text. Currently language support has been added for `English`, `Hindi`, `Marathi`, `Gujrati`, `Tamil`, `Bengali`

**API Example:**

- ***Example 1: Detecting single city name [english] from message*** 

  - *Python:*

    ```python
    >>> message = 'i want to go to mummbai'
    >>> entity_name = 'city'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> source_language='en'
    
    >>> from ner_v1.chatbot.entity_detection import get_city
    >>> output = get_city(message=message,  entity_name=entity_name,
                          structured_value=structured_value,
                          fallback_value=fallback_value,bot_message=bot_message,
                          language=source_language)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/city/?message=i%20want%20to%20go%20to%20mummbai&entity_name=city&structured_value=&fallback_value=&bot_message=&source_language=en'
    ```
    > **Output ** 

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "mummbai",
          "entity_value": {
            "to": true,
            "via": false,
            "from": false,
            "value": "Mumbai",
            "normal": false
          },
            "language": "en"
        }
      ]
    }
    ```

- ***Example 2: Detecting single city name [Hindi] from message***

  - *Python:*

    ```python
    >>> message = u"मुझे दिल्ली की फ्लाइट करनी है"
    >>> entity_name = 'city'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> source_language='hi'
    
    >>> from ner_v1.chatbot.entity_detection import get_city
    >>> output = get_city(message=message, entity_name=entity_name,
                          structured_value=structured_value,
                          fallback_value=fallback_value,bot_message=bot_message,
                          language=source_language)
    >>> print(output)
    ```

  - *CURL command:*

    ```bash
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/city/?message=मुझे%20दिल्ली%20की%20फ्लाइट%20करनी%20है&entity_name=city&structured_value=&fallback_value=&bot_message=&source_language=hi'
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": u"दिल्ली",
          "entity_value": {
            "to": true,
            "via": false,
            "from": false,
            "value": u"दिल्ली",
            "normal": false
          },
            "language": "hi"
        }
      ]
    }
    ```

- ***Example 3: Detecting multiple city name [English] from message***

  - *Python*

    ```python
    >>> message = 'i want to book a flight from delhhi to mumbai'
    >>> entity_name = 'city'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> source_language='en'
    
    >>> from ner_v1.chatbot.entity_detection import get_city
    >>> output = get_city(message=message, entity_name=entity_name,
                          structured_value=structured_value,
                          fallback_value=fallback_value,bot_message=bot_message,
                          language=source_language)
    >>> print(output)
    ```

  - *Curl Command*

    ```bash
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/city/?message=i%20want%20book%20flight%20flight%20from%20delhhi%20to%20mumbai&entity_name=city&structured_value=&fallback_value=&bot_message=&source_language=en'
    ```
    > **Output **:

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "delhhi",
          "entity_value": {
            "to": false,
            "via": false,
            "from": true,
            "value": "New Delhi",
            "normal": false
          },
          "language": "en"
        },
        {
          "detection": "message",
          "original_text": "mumbai",
          "entity_value": {
            "to": true,
            "via": false,
            "from": false,
            "value": "Mumbai",
            "normal": false
          },
          "language": "en"
        }
      ]
    }
    ```

- ***Example 4: Detecting city name [English] using bot message as context.***

  - *Python*

    ```python
    >>> message = "mummbai"
    >>> entity_name = 'city'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = "Please help me departure city?"
    >>> source_language="en"
    
    >>> from ner_v1.chatbot.entity_detection import get_city
    >>> output = get_city(message=message, entity_name=entity_name,
                          structured_value=structured_value,
                          fallback_value=fallback_value,bot_message=bot_message,
                          langauge=source_language)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/city/?message=mummbai&entity_name=city&structured_value=&fallback_value=&bot_message=Please%20help%20me%20departure%20city%3F&source_language=en'
    ```

    > **Output **:

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "mummbai",
          "entity_value": {
            "to": false,
            "via": false,
            "from": true,
            "value": "Mumbai",
            "normal": false
          },
           "language": "en"
        }
      ]
    }
    ```



### 5. PNR Number

> *entity_type: pnr*

The PNR Detector has the capability to detect Train/ Flight PNR number within the given text. 

**API Examples**:

- ***Example 1: Detecting 10 digit Train PNR number from text***

  - *Python*

    ```python
    >>> entity_name = 'train_pnr'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    
    >>> from ner_v1.chatbot.entity_detection import get_pnr
    >>> output = get_pnr(message=message, entity_name=entity_name,
                         structured_value=structured_value,
                         fallback_value=fallback_value, bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```bash
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/pnr/?message=check%20my%20pnr%20status%20for%202141215305.&entity_name=pnr&structured_value=&fallback_value=&bot_message='
    ```

    > **Output**:

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "2141215305",
          "entity_value": {
            "value": "2141215305"
          }
        }
      ]
    }
    ```

    

### 6. Number Entity

> entity_type: number

The Number detector module has the capability to detect number or number word from text in multiple languages. The detector supports an additional feature of detecting units along with number if given in text. For example -  for a given text `5 kg`, this module will return `5`  as detected value and `kg` as detected unit.  It also has the capability to detect only certain type of numbers like currency or temperature type numbers by specifying the unit type. 

Currently number detection support has been provided for 6 different languages - `English`,  `Hindi`, `Marathi`,  `Bengali`,  `Gujrati`, `Tamil`. It also supports latin script of given languages.

> To add support for new languages or to add custom patterns in particular language please go through the Number Detector readme [here](https://github.com/hellohaptik/chatbot_ner/blob/develop/ner_v2/detectors/numeral/number/README.md)

*Note - This module has been updated to v2 version of chatbot_ner.*

**API Example**:

- ***Example 1: Detecting number[English] without unit in message***

  - *Python*

    ```python
    # For a sample query with following parameters
    >>> message="i want to purchase 30 units of mobile abd 40 units of telivision"
    >>> entity_name='number'
    >>> structured_value=None
    >>> fallback_value=None
    >>> bot_message=None
    >>> min_number_digits=1  # minimum number of digit 
    >>> max_number_digits=6  # maximum number of digit
    >>> source_language='en' # here language will be ISO 639-1 code
    >>> unit_type=None       # this restrict the number detector to detect particular 
    						 # number type only.
    
    >>> from ner_v2.detector.number.number.number_detection import NumberDetector
    >>> detector = NumberDetector(entity_name=entity_name, language=source_language, 
                                 unit_type=None)  
    >>> detector.set_min_max_digits(min_digit=min_number_digits,
                                    max_digit=max_number_digits) 
    >>> output = detector.detect(message=message,structured_value=structured_value,
                                fallback_value=fallback_value,
                                bot_message=bot_message)
    >> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/number/?message=I%20want%20to%20purchase%2030%20units%20of%20mobile%20and%2040%20units%20of%20Television&entity_name=number_of_unit&structured_value=&fallback_value=&bot_message=&min_number_digits=1&max_number_digits=2&source_language=en&unit_type='
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "30",
          "entity_value": {
              "value": "30",
              "unit": null
          },
            "language": "en"
        },
        {
          "detection": "message",
          "original_text": "40",
          "entity_value": {
              "value": "40",
              "unit": null
          },
            "language": "en"
        }
      ]
    }
    ```

- ***Example 2: Detecting number[Hindi] without unit in message***

  - *Python*

    ```python
    # For a sample query with following parameters
    >>> message="मुझे ३० किलो आटा और दो हजार का चीनी देना "
    >>> entity_name='number'
    >>> structured_value=None
    >>> fallback_value=None
    >>> bot_message=None
    >>> min_number_digits=1  # minimum number of digit 
    >>> max_number_digits=6  # maximum number of digit
    >>> source_language='hi' # here language will be ISO 639-1 code
    >>> unit_type=None       # this restrict the number detector to detect particular 
    						 # number type only.
    
    >>> from ner_v2.detector.number.number.number_detection import NumberDetector
    >>> detector = NumberDetector(entity_name=entity_name, language=source_language, 
                                 unit_type=None)  
    >>> detector.set_min_max_digits(min_digit=min_number_digits,
                                    max_digit=max_number_digits) 
    >>> output = detector.detect(message=message,structured_value=structured_value,
                                fallback_value=fallback_value,
                                bot_message=bot_message)
    >> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/number/?मुझे%20३०%20किलो%20आटा%20और%20दो%20हजार%20क%20%20चीनी%20देना &entity_name=number_of_unit&structured_value=&fallback_value=&bot_message=&min_number_digits=1&max_number_digits=2&source_language=en&unit_type='
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "३०",
          "entity_value": {
              "value": "30",
              "unit": null
          },
            "language": "hi"
        },
        {
          "detection": "message",
          "original_text": "दो हजार",
          "entity_value": {
              "value": "2000",
              "unit": null
          },
            "language": "hi"
        }
      ]
    }
    ```

- ***Example 3: Detecting number[Hindi in latin script] without unit in message***

  - *Python*

    ```python
    # For a sample query with following parameters
    >>> message="mujhe 30 kilo aata aur 2 hajaar ka chini dena aur teen sau ka chawal"
    >>> entity_name='number'
    >>> structured_value=None
    >>> fallback_value=None
    >>> bot_message=None
    >>> min_number_digits=1  # minimum number of digit 
    >>> max_number_digits=6  # maximum number of digit
    >>> source_language='hi' # here language will be ISO 639-1 code
    >>> unit_type=None       # this restrict the number detector to detect particular 
    						 # number type only.
    
    >>> from ner_v2.detector.number.number.number_detection import NumberDetector
    >>> detector = NumberDetector(entity_name=entity_name, language=source_language, 
                                 unit_type=None)  
    >>> detector.set_min_max_digits(min_digit=min_number_digits,
                                    max_digit=max_number_digits) 
    >>> output = detector.detect(message=message,structured_value=structured_value,
                                fallback_value=fallback_value,
                                bot_message=bot_message)
    >> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/number/?mujhe%2030%20kilo%20aata%20aur%202%20hajaar%20ka%20chini%20dena%20aur%20 teen%20sau%20ka%20chawal&entity_name=number_of_unit&structured_value=&fallback_value=&bot_message=&min_number_digits=1&max_number_digits=2&source_language=en&unit_type='
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "30",
          "entity_value": {
              "value": "30",
              "unit": null
          },
            "language": "hi"
        },
        {
          "detection": "message",
          "original_text": "2 hajaar",
          "entity_value": {
              "value": "2000",
              "unit": null
          },
            "language": "hi"
        },
           {
          "detection": "message",
          "original_text": "teen sau",
          "entity_value": {
              "value": "300",
              "unit": null
          },
            "language": "hi"
        }
      ]
    }
    ```

  

- ***Example 4: Detecting number[English] with unit in message***

  - *Python*

    ```python
    # For a sample query with following parameters
    >>> message="i want more than Rupees 20k and 10 pendrive"
    >>> entity_name='number'
    >>> structured_value=None
    >>> fallback_value=None
    >>> bot_message=None
    >>> min_number_digits=1
    >>> max_number_digits=6
    >>> source_language='en' # here language will be ISO 639-1 code
    >>> unit_type='currency'       # this restrict the number detector to detect particular 
    						 # number type only.
    
    >>> from ner_v2.detector.number.number.number_detection import NumberDetector
    >>> detector = NumberDetector(entity_name=entity_name, language=source_language, 
                                 unit_type=None)  
    >>> detector.set_min_max_digits(min_digit=min_number_digits,
                                    max_digit=max_number_digits) 
    >>> output = detector.detect(message=message,structured_value=structured_value,
                                fallback_value=fallback_value,
                                bot_message=bot_message)
    >> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/number/?message=i%20want%20more%20than%20Rupees%2020k%20and%2010%20pendrive&entity_name=number_of_unit&structured_value=&fallback_value=&bot_message=&min_number_digits=1&max_number_digits=2&source_language=en&unit_type=currency'
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "Rupees 20k",
          "entity_value": {
              "value": "20000",
              "unit": "rupees"
          },
            "language": "en"
        }
      ]
    }
    /* here 40 is not detected as unit_type is specified as currency, Hence it only detect numbers having currencies value in unit */ 
    ```

  

### 7. Time Entity

> entity_type: time

The Time detector module has the capability to detect time from text in multiple languages. It can detect time in 12/24 hr format and also detect text with time difference specified. for example - wake me up `after 10 mins`. 

Currently time detection support has been provided in different languages - `English`,  `Hindi`, `Marathi`,  `Bengali`,  `Gujrati`, `Tamil`. It also supports latin script of given languages.

> To add support for new languages or to add custom patterns in particular language please go through the Time Detector readme [here](https://github.com/hellohaptik/chatbot_ner/blob/develop/ner_v2/detectors/temporal/time/README.md)

*Note - This module has been updated to v2 version of chatbot_ner.*

**API Example**:
- ***Example 1: Detect time[English] from text having 24 hrs, 12 hrs and time difference time format***

  - *Python*

    ```python
    >>> message = "John arrived at the bus stop at 13:50 hrs, expecting the bus to be there in 15 mins. But the bus was scheduled for 12:30 pm"
    >>> entity_name = 'time'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> timezone = 'UTC' 
    >>> source_language='en'
    
    >>> from ner_v2.detectors.temporal.time.time_detection import TimeDetector
    >>> detector = TimeDetector(entity_name=entity_name, language=source_language, 
                                timezone=timezone)  
    >>> output = detector.detect(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value)
    >>> print(output)
    ```

  - *CURL command*

    ```bash
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/time/?message=John%20arrived%20at%20the%20bus%20stop%20at%2013%3A50%20hrs%2C%20expecting%20the%20bus%20to%20be%20there%20in%2015%20mins.%20But%20the%20bus%20was%20scheduled%20for%2012%3A30%20pm&entity_name=time&structured_value=&fallback_value=&bot_message=&timezone=UTC&source_language=en'
    ```

    > **Output**:
    >
    > ```json
    > {
    >   "data": [
    >     {
    >       "detection": "message",
    >       "original_text": "12:30 pm",
    >       "entity_value": {
    >         "mm": 30,
    >         "hh": 12,
    >         "nn": "pm"
    >       },
    >         "language": "en"
    >     },
    >     {
    >       "detection": "message",
    >       "original_text": "in 15 mins",
    >       "entity_value": {
    >         "mm": "15",
    >         "hh": 0,
    >         "nn": "df"
    >       },
    >         "language": "en"
    >     },
    >     {
    >       "detection": "message",
    >       "original_text": "13:50",
    >       "entity_value": {
    >         "mm": 50,
    >         "hh": 13,
    >         "nn": "hrs"
    >       },
    >         "language": "en"
    >     }
    >   ]
    > }
    > ```



- ***Example 2: Detect time[Hindi] from text containing 24 hrs, 12 hrs and time difference text format***

  - *Python*

    ```python
    >>> message = "राजू का बस १३:५० को बस स्टॉप से निकला और १५ मिनट में यहाँ पहुंच जाएगा और गोवा को शाम में बारह बजकर ३० मिनट पैर पहुंचेगा"
    >>> entity_name = 'time'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> timezone = 'UTC' 
    >>> source_language='hi'
    
    >>> from ner_v2.detectors.temporal.time.time_detection import TimeDetector
    >>> detector = TimeDetector(entity_name=entity_name, language=source_language, 
                                timezone=timezone)  
    >>> output = detector.detect(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value)
    >>> print(output)
    ```

  - *CURL command*

    ```bash
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/time/?message=राजू%20का%20बस%20१३:५०%20को%20बस%20स्टॉप%20से%20निकला%20और%20१५%20मिनट%20में%20यहाँ%20पहुंच%20जाएगा%20और%20गोवा%20को%20शाम%20में%20बारह%20बजकर%20३०%20मिनट%20पैर%20पहुंचेगा&entity_name=time&structured_value=&fallback_value=&bot_message=&timezone=UTC&source_language=en'
    ```

    > **Output**:
    >
    > ```json
    > {
    >   "data": [
    >     {
    >       "detection": "message",
    >       "original_text": "१३:५०",
    >       "entity_value": {
    >         "mm": 1,
    >         "hh": 50,
    >         "nn": "hr"
    >       },
    >         "language": "hi"
    >     },
    >     {
    >       "detection": "message",
    >       "original_text": "१५ मिनट में",
    >       "entity_value": {
    >         "mm": "15",
    >         "hh": 0,
    >         "nn": "df"
    >       },
    >         "language": "hi"
    >     },
    >     {
    >       "detection": "message",
    >       "original_text": "शाम में बारह बजकर ३० मिनट",
    >       "entity_value": {
    >         "mm": 30,
    >         "hh": 12,
    >         "nn": "pm"
    >       },
    >         "language": "hi"
    >     }
    >   ]
    > }
    > ```



### 8. Time with range 

> entity_type: time_with_range

The Time with range detector module has the capability to detect range of time with start and end range from  text. It supports all 24 hrs and 12hr time format. It currently supports only english language.

**API Example**:

- ***Example 1: Detect time range from message***

  Use the **timezone** parameter to pass your current timezone to time detection

  - *Python:*

    ```python
    >>> message = 'Set a drink water reminder for tomorrow from 7:00 AM to 6:00 PM'
    >>> entity_name = 'time_with_range'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> timezone = 'UTC'  
    
    >>> from ner_v1.chatbot.entity_detection import get_time_with_range
    >>> output = get_time_with_range(message=message, entity_name=entity_name,
                                     structured_value=structured_value,
                                     fallback_value=fallback_value,
                                     bot_message=bot_message, timezone=timezone)
    >>> print(output)
    ```

  - *CURL command:*

    ```bash
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/time_with_range/?message=Set+a+drink+water+reminder+for+tomorrow+from+7%3A00+AM+to+6%3A00+PM&entity_name=time_with_range&structured_value=&fallback_value=&bot_message=&timezone=UTC'
    ```

    

    >  **Output**:
    >
    > ```json
    > {  
    > "data": [
    >     {
    >       "detection": "message", 
    >       "original_text": "7:00 am to 6:00 pm", 
    >       "entity_value": {
    >          "mm": 0, 
    >          "hh": 7, 
    >          "range": "start", 
    >          "nn": "am", 
    >          "time_type": null
    >       }, 
    >       "language": "en"
    >     }, 
    >     {
    >       "detection": "message",
    >       "original_text": "7:00 am to 6:00 pm", 
    >       "entity_value": {
    >         "mm": 0, 
    >         "hh": 6, 
    >         "range": "end", 
    >         "nn": "pm", 
    >         "time_type": null
    >       }, 
    >       "language": "en"
    >     }
    >     ]
    > }
    > ```




### 9. Date Entity

> entity_type: date

The Date detector module has the capability to detect various form of dates from text in multiple languages. It can detect date from following patterns:

 	1. *Day month year format*  - 12 feb 2018, 2nd Jan 2019,  12/11/2019, 12-jan-2019
		2. *Day month* - 12 feb, 12/12
		3. Weekday reference - Comming monday, next sunday
		4. Reference day month - 2nd of next month, 2nd sunday of coming month
		5. Current day reference -  tomorrow, yesterday, day after tomorrow

 Currently time detection support has been provided in different languages - `English`,  `Hindi`, `Marathi`,  `Bengali`,  `Gujrati`, `Tamil`. It also supports latin script of given languages.

> To add support for new languages or to add custom patterns in particular language please go through the Date Detector readme [here](https://github.com/hellohaptik/chatbot_ner/blob/develop/ner_v2/detectors/temporal/date/README.md)

*Note - This module has been updated to v2 version of chatbot_ner*

**API Examples:**

- ***Example 1: Detecting day month format date [English] from user message***

  Use the **timezone** parameter to pass your current timezone to date detection

  - *Python:*

    ```python
    >>> message = "set me reminder on 23rd december"
    >>> entity_name = 'date'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> timezone='UTC'
    >>> source_language='en'
    >>> past_date_referenced=False # flag to check if the date reference lies in past 				   				  or future. For Example - In hindi "Kal" ``									corresonds to both tomorrow and yesterday. So 									this flag will determines actual referenced date. 
    
    >>> from ner_v2.detectors.temporal.date.date_detection import DateAdvanceDetector
    >>> detector = DateAdvanceDetector(entity_name=entity_name,
                                       language=source_language, 
                                       timezone=timezone,
                                       past_date_referenced=past_date_referenced)  
    >>> output = detector.detect(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value)
    >>> print(output)
    ```

  - *CURL:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/date/?message=set%20me%20reminder%20on%2023rd%20december&entity_name=date&structured_value=&fallback_value=&bot_message=%timezone=UTC&source_language=en&past_date_referenced=false'
    ```

    >  **Output:**

    ```json
    {
        "data": [
          {
            "detection": "message",
            "original_text": "23rd december",
            "entity_value": {
              "end_range": false,
              "from": false,
              "normal": true,
              "to": false,
              "start_range": false,
              
              "value": {
                "mm": 12,
                "yy": 2017,
                "dd": 23,
                "type": "date"
              }
            },
              "language": "en"
          }
        ]
     }
    ```

- ***Example 2: Detecting  referenced date [Hindi] from user message***

  Use the **timezone** parameter to pass your current timezone to date detection

  - *Python:*

    ```python
    >>> message = "मुझे कल सुबह ५ बजे उठा देना"
    >>> entity_name = 'date'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> timezone='UTC'
    >>> source_language='hi'
    >>> past_date_referenced=False 
    >>> from ner_v2.detectors.temporal.date.date_detection import DateAdvanceDetector
    >>> detector = DateAdvanceDetector(entity_name=entity_name,
                                       language=source_language, 
                                       timezone=timezone,
                                       past_date_referenced=past_date_referenced)  
    >>> output = detector.detect(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value)
    >>> print(output)
    ```

  - *CURL:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/date/?message=मुझे%20कल%20सुबह%20५%20बजे%20उठा%20देना&entity_name=date&structured_value=&fallback_value=&bot_message=%timezone=UTC&source_language=en&past_date_referenced=false'
    ```

    >  **Output:**

    ```json
    /* Assuming today's date is 12th feb 2019*/
    {
        "data": [
          {
            "detection": "message",
            "original_text": "कल",
            "entity_value": {
              "end_range": false,
              "from": false,
              "normal": true,
              "to": false,
              "start_range": false,
              
              "value": {
                "mm": 2,
                "yy": 2019,
                "dd": 13,
                "type": "date"
              }
            },
              "language": "hi"
          }
        ]
     }
    ```

- ***Example 3: Detecting  referenced weekday [Hindi] from user message***

  Use the **timezone** parameter to pass your current timezone to date detection

  - *Python:*

    ```python
    >>> message = "आने वाले सोमवार को मेरा मैथ्स का एग्जाम है"
    >>> entity_name = 'date'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> timezone='UTC'
    >>> source_language='hi'
    >>> past_date_referenced=False 
    >>> from ner_v2.detectors.temporal.date.date_detection import DateAdvanceDetector
    >>> detector = DateAdvanceDetector(entity_name=entity_name,
                                       language=source_language, 
                                       timezone=timezone,
                                       past_date_referenced=past_date_referenced)  
    >>> output = detector.detect(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value)
    >>> print(output)
    ```

  - *CURL:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v2/date/?message=आने%20वाले%20सोमवार%20को%20मेरा%20मैथ्स%20का%20एग्जाम%20है&entity_name=date&structured_value=&fallback_value=&bot_message=%timezone=UTC&source_language=en&past_date_referenced=false'
    ```

    >  **Output:**

    ```json
    /* Assuming today's date is 12th feb 2019*/
    {
        "data": [
          {
            "detection": "message",
            "original_text": "आने वाले सोमवार",
            "entity_value": {
              "end_range": false,
              "from": false,
              "normal": true,
              "to": false,
              "start_range": false,
              
              "value": {
                "mm": 2,
                "yy": 2019,
                "dd": 18,
                "type": "date"
              }
            },
              "language": "hi"
          }
        ]
     }
    ```



### 10. Budget

> entity_type: budget

The budget detector module helps to detect start and end range of amount from given text. Currently it detect indian currency range only.

**API Example:**

- ***Example 1: Detect budget from text containing both min and max value***

  - *Python:*

    ```python
    >>> message = "shirts between 2000 to 3000"
    >>> entity_name = 'budget'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> from ner_v1.chatbot.entity_detection import get_budget
    >>> output =get_budget(message=message,
                           entity_name=entity_name,
                           structured_value=structured_value,
                           fallback_value=fallback_value, bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/budget/?message=shirts%20between%202000%20to%203000&entity_name=budget&structured_value=&fallback_value=&bot_message='
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "2000 to 3000",
          "entity_value": {
            "max_budget": 3000,
            "type": "normal_budget",
            "min_budget": 2000
          }
        }
      ]
    }
    ```

- ***Example 2: Detect budget from text containing only max value***

  - *Python:*

    ```python
    >>> message = "I want to buy shoes in less than 200 rupees"
    >>> entity_name = 'budget'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    >>> from ner_v1.chatbot.entity_detection import get_budget
    >>> output =get_budget(message=message,
                           entity_name=entity_name,
                           structured_value=structured_value,
                           fallback_value=fallback_value, bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/budget/?message=I%20want%20to%20buy%20shoes%20in%20less%20than%20200rupees&entity_name=budget&structured_value=&fallback_value=&bot_message='
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "2000 to 3000",
          "entity_value": {
            "max_budget": 3000,
            "type": "normal_budget",
            "min_budget": 2000
          }
        }
      ]
    }
    ```




### 11. Apparel's Shopping Size

> entity_type: shopping_size

This functionality helps to detect cloth size for different apparel from given text. For example, Large, small, 34, etc.

**API Examples:**

- ***Example 1: Detect shopping size for different apparel type from given text.*** 

  - *Python:*

    ```python
    >>> message = "I want to buy Large shirt and jeans of 36 waist"
    >>> entity_name = 'shopping_clothes_size'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    
    >>> from ner_v1.chatbot.entity_detection import get_shopping_size
    >>> output = get_shopping_size(message=message, entity_name=entity_name,
                                   structured_value=structured_value,
                                   fallback_value=fallback_value,
                                   bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/shopping_size/?message=I%20want%20to%20buy%20Large%20shirt%20and%20jeans%20of%2036%20waist&entity_name=shopping_clothes_size&structured_value=&fallback_value=&bot_message='
    ```
    > **Output**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "large",
          "entity_value": {
            "value": "L"
          }
        },
        {
          "detection": "message",
          "original_text": "36",
          "entity_value": {
            "value": "36"
          }
        }
      ]
    }
    ```




### 12. Passenger Count

> entity_type: passenger_count

This functionality help to detect passenger count from given text. For example `3 people`, `2 passenger`,`2 traveller`

**API Example:**

- ***Example 1: Detect number of passenger from given user message.***

  - *Python:*

    ```python
    >>> message = 'Can you please help me to book tickets for 3 people'
    >>> entity_name = 'no_of_adults'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    
    >>> from ner_v1.chatbot.entity_detection import get_passenger_count
    >>> output = get_passenger_count(message=message, entity_name=entity_name,
                                     structured_value=structured_value,
                                     fallback_value=fallback_value,
                                     bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/passenger_count/?message=Can+you+please+help+me+to+book+tickets+for+3+people&entity_name=no_of_adults&structured_value=&fallback_value=&bot_message='
    ```

    >  **Output**:

    ```json
    {
      "data": [
        {
          "detection": "message", 
          "original_text": "3", 
          "entity_value": {
            "value": "3"
          }, 
          "language": "en"
        }
      ]
    }
    ```




### 13. Location Entity

> entity_type: locality

This functionality helps to detect locality from given text. For example - Andheri west, goregaon (These are locality places in Mumbai [city in India])

**API Example:**

- ***Example 1: Detecting location from user message***

  - *Python:*

    ```python
    >>> message = 'atm in andheri west'
    >>> entity_name = 'locality_list'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = None
    
    >>> from ner_v1.chatbot.entity_detection import get_location
    >>> output = get_location(message=message, entity_name=entity_name,
                              structured_value=structured_value,
                              fallback_value=fallback_value, bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL command:*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/location/?message=atm+in+andheri+west&entity_name=locality_list&structured_value=&fallback_value=&bot_message='
    ```

    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message", 
          "original_text": "andheri west", 
          "entity_value": {
            "value": "Andheri West"
          }, 
          "language": "en"
        }
      ]
    }
    ```




### 14. Person Name

> entity_type: person_name

This functionality helps to detect person's name from given text.

**API Examples:**

- ***Example 1: Detect person's name from user message***

  - *Python:*

    ```python
    >>> message = 'my name is yash doshi'
    >>> entity_name = 'person_name'
    >>> structured_value = None
    >>> fallback_value = 'Guest'
    >>> bot_message = 'what is your name ?'
    
    >>> from ner_v1.chatbot.entity_detection import get_person_name
    >>> output = get_person_name(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value,
                                 bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL :*

    ```python
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/person_name/?message=my%20name%20is%yash%20doshi&entity_name=person_name&structured_value=&fallback_value=Guest&bot_message=what%20is%your%20name%20?'
    ```

    >  **Output:**

    ```python
    {
      "data": [
        {
          "detection": "message",
          "original_text": "yash doshi",
          "entity_value": {
            "first_name": "yash",
            "last_name": "doshi",
            "middle_name": null
            
          }
        }
      ]
    }
    ```

- ***Example 2: Detect person's name from fallback value***

  - *Python:*

    ```python
    >>> message = ''
    >>> entity_name = 'person_name'
    >>> structured_value = None
    >>> fallback_value = 'sagar nimesh dedhia'
    >>> bot_message = 'what is your name ?'
    
    >>> from ner_v1.chatbot.entity_detection import get_person_name
    >>> output = get_person_name(message=message, entity_name=entity_name,
                                 structured_value=structured_value,
                                 fallback_value=fallback_value,
                                 bot_message=bot_message)
    >>> print(output)
    ```

  - *CURL :*

    ```shell
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/person_name/?message=&entity_name=person_name&structured_value=&fallback_value=sagar%20nimesh%20dedhia&bot_message=what%20is%your%20name%20?'
    ```
    > **Output:**

    ```json
    {
      "data": [
        {
          "detection": "fallback_value",
          "original_text": "sagar nimesh dedhia",
          "entity_value": {
            "first_name": "sagar"
            "last_name": "dedhia"
            "middle_name": "nimesh"
          }
        }
      ]
    }
    ```


### 15. Regex Entity

> entity_type: regex

This functionality helps to detect  entities that abide by the specified regex.

*IMPORTANT NOTES*

 - *The regex pattern provided must be escaped if you are not passing in a raw string (marked by 'r' in Python)*
 - *Errors in compiling the provided pattern are not handled and will result in an exception*
 - *chatbot_ner also uses re.UNICODE flag by default for detection. This can be overridden by using re_flags argument in the constructor*
 - *If you are using groups, only 0th group will be returned. Sub grouping is not supported at the moment*

**API Examples**:

- ***Example 1: Detecting 4-6 digit number using regex***

  - *Python:*

    ```python
    >>> message = '123456 is my otp'
    >>> entity_name = 'regex_test_otp'
    >>> structured_value = None
    >>> fallback_value = None
    >>> bot_message = 'enter the otp'
    >>> regex = '\\d{4,6}'
    
    >>> from ner_v1.chatbot.entity_detection import get_regex
    >>> output = get_regex(message=message,entity_name=entity_name,
                           structured_value=structured_value,
                           fallback_value=fallback_value,bot_message=bot_message,
                           pattern=regex)
    >>> print(output)
    ```

  - *CURL command:*

    ```bash
    URL='localhost'
    PORT=8081
    
    curl -i 'http://'$URL':'$PORT'/v1/regex/?message=123456%20is%20my%otp&entity_name=regex&structured_value=&fallback_value=&bot_message=enter%20the%otp%20&regex=\d{4,6}'
    ```

    >  **Output:**

    ```json
    {
      "data": [
        {
          "detection": "message",
          "original_text": "123456",
          "entity_value": "123456"
        }
       ]
    }
    ```


  ​

## Data Tagging

This functionality tags the message with the entity name and also identifies the entity values.

**API Example:**

- *CURL command:*

  ```shell
  entities = ['date','time','restaurant']
  message = "Reserve me a table today at 6:30pm at Mainland China and on Monday at 7:00pm at Barbeque Nation"
  
  URL='localhost'
  PORT=8081
  
  curl -i 'http://'$URL':'$PORT'/v1/ner/?entities=\[%22date%22,%22time%22,%22restaurant%22\]&message=Reserve%20me%20a%20table%20today%20at%206:30pm%20at%20Mainland%20China%20and%20on%20Monday%20at%207:00pm%20at%20Barbeque%20Nation'
  ```

  >  **Output:**

  ```json
  {
    "data": {
      "tag": "reserve me a table __date__ at __time__ at __restaurant__ and on __date__ at __time__ at __restaurant__",
      "entity_data": {
        "date": [
          {
            "detection": "message",
            "original_text": "monday",
            "entity_value": {
              "mm": 3,
              "yy": 2017,
              "dd": 27,
              "type": "day_within_one_week"
            }
          },
          {
            "detection": "message",
            "original_text": "today",
            "entity_value": {
              "mm": 3,
              "yy": 2017,
              "dd": 21,
              "type": "today"
            }
          }
        ],
        "time": [
          {
            "detection": "message",
            "original_text": "6:30pm",
            "entity_value": {
              "mm": 30,
              "hh": 6,
              "nn": "pm"
            }
          },
          {
            "detection": "message",
            "original_text": "7:00pm",
            "entity_value": {
              "mm": 0,
              "hh": 7,
              "nn": "pm"
            }
          }
        ],
        "restaurant": [
          {
            "detection": "message",
            "original_text": "barbeque nation",
            "entity_value": {
              "value": "Barbeque Nation"
            }
          },
          {
            "detection": "message",
            "original_text": "mainland china",
            "entity_value": {
              "value": "Mainland China"
            }
          }
        ]
      }
    }
  }
  ```


