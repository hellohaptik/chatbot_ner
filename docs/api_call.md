
# API calls

[TOC]

## List of entity types

Following are the list of different entity types along with its API call:

### text

- This functionality calls the TextDetection class to detect textual entities.

- Example:

  - Example 1: 

    - ```python
      message='i want to order chinese from  mainland china and pizza from domminos'
      entity_name='restaurant'
      structured_value=None
      fallback_value=None
      bot_message=None
      ```

    - *Python:* 

      ```python
      from ner_v1.chatbot.entity_detection import get_text
      output = get_text(message=message, entity_name=entity_name, structured_value=structured_value, fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/text/?message=i%20want%20to%20order%20chinese%20from%20%20mainland%20china%20and%20pizza%20from%20domminos&entity_name=restaurant&structured_value=&fallback_value=None&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "mainland china",
            "entity_value": {
              "value": "Mainland China"
            }
          },
          {
            "detection": "message",
            "original_text": "domminos",
            "entity_value": {
              "value": "Domino's Pizza"
            }
          }
        ]
      }
      ```

  - Example 2: 

    - ```python
      message = 'i wanted to watch movie'
      entity_name = 'movie'
      structured_value = 'inferno'
      fallback_value = None
      bot_message = None
      ```

    - *Python:* 

      ```python
      from ner_v1.chatbot.entity_detection import get_text
      output = get_text(message=message, entity_name=entity_name, structured_value=structured_value, fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/text/?message=i%20wanted%20to%20watch%20movie&entity_name=movie&structured_value=inferno&fallback_value=None&bot_message='
      ```

    - *CURL Output*:

    - ​

      ```json
      {
        "data": [
          {
            "detection": "structure_value_verified",
            "original_text": "inferno",
            "entity_value": {
              "value": "Inferno"
            }
          }
        ]
      }
      ```

  - ​


### phone_number

- This functionality calls the PhoneDetector class to detect textual entities.

- Example:

  - Example 1: 

    - ```python
      message = 'my contact number is 9049961794'
      entity_name = 'phone_number'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:* 

      ```python
      from ner_v1.chatbot.entity_detection import get_phone_number
      output = get_phone_number(message=message,entity_name=entity_name,                   structured_value=structured_value,fallback_value=fallback_value,bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/phone_number/?message=my%20contact%20number%20is%209049961794&entity_name=phone_number&structured_value=&fallback_value=None&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "9049961794",
            "entity_value": {
              "value": "9049961794"
            }
          }
        ]
      }
      ```

  - Example 2: 

    - ```python
      message = 'Please call me'
      entity_name = 'phone_number'
      structured_value = None
      fallback_value = '9049961794'
      bot_message = None
      ```

    - *Python:* 

      ```python
      from ner_v1.chatbot.entity_detection import get_phone_number
      output = get_phone_number(message=message,entity_name=entity_name,                   structured_value=structured_value,fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ​

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/phone_number/?message=Please%20call%20me&entity_name=phone_number&structured_value=&fallback_value=9049961794&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "fallback_value",
            "original_text": "9049961794",
            "entity_value": {
              "value": "9049961794"
            }
          }
        ]
      }
      ```

### email

- This functionality calls the EmailDetector class to detect email ids.

- Example:

  - Example 1: 

    - ```python
      message = 'my email id is apurv.nagvenkar@gmail.com'
      entity_name = 'email'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_email
      output = get_email(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/email/?message=my%20email%20id%20is%20apurv.nagvenkar%40gmail.com&entity_name=email&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "apurv.nagvenkar@gmail.com",
            "entity_value": {
              "value": "apurv.nagvenkar@gmail.com"
            }
          }
        ]
      }
      ```

  - Example 2: 

    - ```python
      message = 'send me to my email'
      entity_name = 'email'
      structured_value = None
      fallback_value = 'apurv.nagvenkar@gmail.com'
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_email
      output = get_email(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/email/?message=send%20me%20to%20my%20email&entity_name=email&structured_value=&fallback_value=apurv.nagvenkar@gmail.com&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "fallback_value",
            "original_text": "apurv.nagvenkar@gmail.com",
            "entity_value": {
              "value": "apurv.nagvenkar@gmail.com"
            }
          }
        ]
      }
      ```

### city

- This functionality calls the CityDetector class to detect cities along with its attributes.

- Example:

  - Example 1: 

    - ```python
      message = 'i want to go to mummbai'
      entity_name = 'city'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_city
      output = get_city(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value,bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/city/?message=i%20want%20to%20go%20to%20mummbai&entity_name=city&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

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
            }
          }
        ]
      }
      ```

  - Example 2:

    - ```python
      message = "I want to book a flight from delhhi to mumbai"
      entity_name = 'city'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_city
      output = get_city(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value,bot_message=bot_message)
      print output
      ```

    - CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/city/?message=I%20want%20to%20book%20a%20flight%20from%20delhhi%20to%20mumbai&entity_name=city&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

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
            }
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
            }
          }
        ]
      }
      ```

  - Example 3:

    - ```python
      message = "mummbai"
      entity_name = 'city'
      structured_value = None
      fallback_value = None
      bot_message = "Please help me departure city?"
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/city/?message=mummbai&entity_name=city&structured_value=&fallback_value=&bot_message=Please%20help%20me%20departure%20city%3F'
      ```

    - *CURL Output:*

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
            }
          }
        ]
      }
      ```

### pnr

-   This functionality calls the PNRDetector class to detect pnr.

-   Example:

-   - Example 1: 

    - ```python
      message = 'check my pnr status for 2141215305.'
      entity_name = 'train_pnr'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_pnr
      output = get_pnr(message=message, entity_name=entity_name,structured_value=structured_value,fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/pnr/?message=check%20my%20pnr%20status%20for%202141215305.&entity_name=pnr&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

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

### number

- This functionality calls the NumberDetector class to detect numerals.

- Example:

  - Example 1:

    - ```python
      message = "I want to purchase 30 units of mobile and 40 units of Television"
      entity_name = 'number_of_unit'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_number
      output = get_number(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value,bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/number/?message=I%20want%20to%20purchase%2030%20units%20of%20mobile%20and%2040%20units%20of%20Television&entity_name=number_of_unit&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "30",
            "entity_value": {
              "value": "30"
            }
          },
          {
            "detection": "message",
            "original_text": "40",
            "entity_value": {
              "value": "40"
            }
          }
        ]
      }
      ```

  - Example 2:

    - ```python
      message = "I want to reserve a table for 3 people"
      entity_name = 'number_of_people'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_number
      output = get_number(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value,bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/number/?message=I%20want%20to%20reserve%20a%20table%20for%203%20people&entity_name=number_of_people&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "for 3 people",
            "entity_value": {
              "value": "3"
            }
          }
        ]
      }
      ```

### time

- This functionality calls the TimeDetector class to detect time.

- Example:

  - Example 1:

    - ```python
      message = "John arrived at the bus stop at 13:50 hrs, expecting the bus to be there in 15 mins. \
      But the bus was scheduled for 12:30 pm"
      entity_name = 'time'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_time
      output = get_time(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value,bot_message=bot_message)
      print output
      ```

    - CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/time/?message=John%20arrived%20at%20the%20bus%20stop%20at%2013%3A50%20hrs%2C%20expecting%20the%20bus%20to%20be%20there%20in%2015%20mins.%20But%20the%20bus%20was%20scheduled%20for%2012%3A30%20pm&entity_name=time&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "12:30 pm",
            "entity_value": {
              "mm": 30,
              "hh": 12,
              "nn": "pm"
            }
          },
          {
            "detection": "message",
            "original_text": "in 15 mins",
            "entity_value": {
              "mm": "15",
              "hh": 0,
              "nn": "df"
            }
          },
          {
            "detection": "message",
            "original_text": "13:50",
            "entity_value": {
              "mm": 50,
              "hh": 13,
              "nn": "hrs"
            }
          }
        ]
      }
      ```

### date

- This functionality calls the DateDetector class to detect date.

- Example:

  - Example 1:

    - ```python
      message = "set me reminder on 23rd december"
      entity_name = 'date'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_date
      output = get_date(message=message, entity_name=entity_name, structured_value=structured_value, fallback_value=fallback_value,bot_message=bot_message)
      print output
      ```

    - CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/date/?message=set%20me%20reminder%20on%2023rd%20december&entity_name=date&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "23rd december",
            "entity_value": {
              "mm": 12,
              "yy": 2017,
              "dd": 23,
              "type": "date"
            }
          }
        ]
      }
      ```

  - Example 2:

    - ```python
      message = "set me reminder day after tomorrow"
      entity_name = 'date'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/date/?message=set%20me%20reminder%20day%20after%20tomorrow&entity_name=date&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "day after tomorrow",
            "entity_value": {
              "mm": 3,
              "yy": 2017,
              "dd": 22,
              "type": "day_after"
            }
          }
        ]
      }
      ```

### budget

- This functionality calls the BudgetDetector class to detect budget.

- Example:

  - Example 1:

    - ```python
      message = "shirts between 2000 to 3000"
      entity_name = 'budget'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_budget
      output = get_budget(message=message, entity_name=entity_name, structured_value=structured_value,fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/budget/?message=shirts%20between%202000%20to%203000&entity_name=budget&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

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

### shopping_size

- This functionality calls the ShoppingSizeDetector class to detect cloth size. For example, Large, small, 34, etc.

- Example:

  - Example 1:

    - ```python

      message = "I want to buy Large shirt and jeans of 36 waist"
      entity_name = 'shopping_size'
      structured_value = None
      fallback_value = None
      bot_message = None
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_shopping_size
      output = get_shopping_size(message=message, entity_name=entity_name, structured_value=structured_value, fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/shopping_size/?message=I%20want%20to%20buy%20Large%20shirt%20and%20jeans%20of%2036%20waist&entity_name=budget&structured_value=&fallback_value=&bot_message='
      ```

    - *CURL Output:*

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

### date_advance

- This functionality calls the DateAdvanceDetector class to detect departure date and arrival date.

- Example:

  - Example 1:

    - ```python
      message = "21st dec"
      entity_name = 'date'
      structured_value = None
      fallback_value = None
      bot_message = 'Please help me with return date?'
      ```

    - *Python:*

      ```python
      from ner_v1.chatbot.entity_detection import get_date_advance
      output = get_date_advance(message=message, entity_name=entity_name, structured_value=structured_value, fallback_value=fallback_value, bot_message=bot_message)
      print output
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/date_advance/?message=21st%20dec&entity_name=date&structured_value=&fallback_value=&bot_message=Please%20help%20me%20with%20return%20date%3F'
      ```

    - *CURL Output:*

      ```json
      {
        "data": [
          {
            "detection": "message",
            "original_text": "21st dec",
            "entity_value": {
              "date_return": {
                "mm": 12,
                "yy": 2017,
                "dd": 21,
                "type": "date"
              },
              "date_departure": null
            }
          }
        ]
      }
      ```

## Data Tagging

- This functionality tags the message with the entity name and also identifies the entity values.

- Example:

  - Example 1:

    - ```python
      entities = ['date','time','restaurant']
      message = "Reserve me a table today at 6:30pm at Mainland China and on Monday at 7:00pm at Barbeque Nation"
      ```

    - *CURL command:*

      ```shell
      URL='localhost'
      PORT=8081
      ```

      ```shell
      curl -i 'http://'$URL':'$PORT'/v1/ner/?entities=\[%22date%22,%22time%22,%22restaurant%22\]&message=Reserve%20me%20a%20table%20today%20at%206:30pm%20at%20Mainland%20China%20and%20on%20Monday%20at%207:00pm%20at%20Barbeque%20Nation'
      ```

    - *CURL Output:*

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

