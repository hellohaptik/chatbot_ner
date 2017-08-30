

# Approach used to build

### **Introduction**

Chatbot is a service, powered by rules and sometimes artificial intelligence (AI), that you interact with via a chat interface. It can be used in applications  ranging from functional to fun. There are several architectures which can be used in the  building chatbot (i.e. Generative based, retrieval based, heuristic based, etc.) and each of this technique somewhere uses entity detection in its pipeline. 

In this repository, we are open-sourcing Named-entity recognition (NER) viz. one of the important module in building the chatbots.

NER is a subtask of information extraction that seeks to locate and classify named entities in text into predefined categories such as the names of persons, organizations, locations, expressions of times, quantities, monetary values, percentages, etc.

For example,

```json
"Remind me to call Mainland China day afer tommorrow at 6:00pm"
```

In this example:

- *Mainland China* is a named entity that belongs to category *restaurant* 
- *day after tommorrow* is a *date* 
- *6:00pm* is a *time*

The current NER is a heuristic based that uses several NLP techniques to extract necessary entities from chat interface. We can also create our own entity and add it to the database which is explained in detail in this [section](adding_entities.md).

In this section of document we have explained the approach and architecture that we have used to extract the entities from the chat interface. 

### Priority of detection

The priority of detecting entity from various modes is shown in following figure:

![chatbot_flow](images/chatbot_flow.png)





1. Run entity detection on [UI elements](terminology.md#ui-elements) because this information is extracted from some structured format.
2. If detection fails on UI element then run detection on a message and return the output.
3. If  it is not able to detect anything from a given message then assign [fallback value](terminology.md#fallback-value) as an output. 

### Entity Detection methods

In chatbot, there are several entities that need to be identified and each entity has to be distinguished based on its type as a different entity has different detection logic. Following is the brief hierarchical representation of the entity classification.  

![entity hierarchy](images/entity_hierarchy.png)



We have classified entities into four main types i.e. *numeral*, *pattern*, *temporal* and *textual*.

- **numeral**: This type will contain all the entities that deal with the numeral or numbers. For example, number detection, budget detection, size detection, etc.  


- **pattern**: This will contain all the detection logics where identification can be done using patterns or regular expressions. For example, email, phone_number, pnr, etc.

- **temporal**: It will contain detection logics for detecting time and date.

- **textual**: It identifies entities by looking at the dictionary. This detection mainly contains detection of text (like cuisine, dish, restaurants, etc.), the name of cities, the location of a user, etc.

  Following are the different detection logics used in detecting entities:

| Entity type   | Class Name           | Description                              | example                                  |
| :------------ | -------------------- | :--------------------------------------- | ---------------------------------------- |
| text          | TextDetector         | Detects custom entities in text string by performing similarity searches against a list fetched from datastore. | Mainland china, Sneakers, La La Land     |
| email         | EmailDetector        | Detects email addresses in given text.   | apurva.n@haptik.ai                       |
| phone_number  | PhoneDetector        | Detects phone numbers in given text.     | +919222222222                            |
| pnr           | PNRDetector          | Detects PNR (serial) codes  in given text. | 4SGX3E, 9876543210                       |
| date          | DateAdvancedDetector | Detects date in various formats from given text. | 28-12-2096, 09th Nov 2014, Tomorrow      |
| city          | CityDetector         | Identifies the city from the text along with its properties | Delhi, Mumbai, from mumbai, mumbai to pune |
| location      | LocationDetector     | Detects location from the text. It is similar to TextDetection but we are trying to improve it with better version. | Andheri, Goregaon                        |
| time          | TimeDetector         | Detects time in various formats from given text. | in 15 mins,  12:30pm, 4:30               |
| budget        | BudgetDetector       | Detects the budget from the text.        | less than 3000, 3-4k,  less than 2k      |
| number        | NumberDetector       | Detects number from the text.            | for 3 people, 30 units                   |
| shopping_size | ShoppingSizeDetector | Detects size which are used for shopping. | XL, large, 34 size                       |

> **NOTE**:  path to the above entity_types -> `ner_v1/entities/`

### Parameters for entity detection

There are several paramters thats needs to be consider while executing detection logic. Following are the list of parameters which are used for detection:

1. **message**: message on which detection logic needs to run. It is an unstructured text from which entity needs to be extracted. For example, *"I want to order pizza"*.

2. **entity_name**: name of the entity. This parameter is important when the detection logic relies on dictionary. It is used to run particular detection logic by looking at its dictionary. 

   For example, in detection logic *get_text()* the entity name is based on which entities we need to detect.

   - For detecting:
     - *cuisine* entity_name will be *"cuisine"*
     - *dish* entity_name will be *"dish"*

   In some detection logic, like *get_phone_number()* entity_name does not have any siginificance as detection logic of phone number won't change based on entity_name. 

3. **structured_value**: It is a value which is obtained from the structured text. For example, UI elements like form,
   payload, etc.

4. **fallback_value**: it is a fallback value. If the detection logic fails to detect any value either from *structured_value* or *message* then we return a *fallback_value* as an output. This value is derived from third party api or from users profile. 

   For example, if user says *"Nearby ATMs"*. In this example user has not provided any information about his location in the chat but, we can pass a *fallback_value* that will contain its location that can be obtained from its profile or third party apis (like geopy, etc).

5. **bot_message**: previous message from a bot/agent. This is an important parameter, many times the entity value relies on the message from the bot/agent i.e. what is bot saying? or asking? 

   For example, bot might ask for departure date to book a flight and user might reply with a date. Now, it is difficult to disambiguate whether its departure date or arrival date unless, we know what bot is asking for?

   ```json
   bot: Please help me with date of departure?
   user: 23rd March
   ```

### Architecture to detect named entities 

Following is the pseudo-code of any entity detection logic:

```python
def func(entity_name, message, structured_value, fallback_value, bot_message):
    detection_object = detection_logic(entity_name=entity_name)
    detection_object.set_bot_message(bot_message)
    if structured_value:
        output = detection_object.detect_entity(text=structured_value)
        if output:
            return output:
        else:
        	return structured_value
    else:
        output = detection_object.detect_entity(text=message)
        if output:
      		return output
        elif fallback_value
      		return fallback_value
    return None
```

First, we initialize the individual entity detection class by passing necessary paramters and do the following: 

1. if *structured_value* is present, then we run the detection logic to extract the necessary information from *structured_value* and return the detected information but, if it fails then we return *stuructured_value* as the output 
2. if *structured_value* is empty then we execute detection logic on the *message* (i.e. unstructured text) and returns the detected output however, if it fails then we return the fallback_value if exisit.

### **Output Format**

The output of entities detected will be stored in a list of dictionary containing the following structure:

```json
[
    {
        "entity_value": entity_value,
        "detection": detection_method,
        "original_text": original_text
    },
]
```

Consider the  following example for detailed explanation:

```latex
"I want to order from mcd"
```

- entity_value: This will store the value of entity (i.e entity value) that is detected. The output will be in dictionary format. For example, `{"value": "McDonalds"}`.
- detection: This will store how the entity is detected i.e. whether from *message*, *structured value* or *fallback value*.
- original_text: This will store the actual value that is detected. For example, mcd.

```json
Example 1:
input:  message = 'i want to order chinese from  mainland china and pizza from domminos'
        entity_name = 'restaurant'
        structured_value = None
        structured_value_verification = 0
        fallback_value = None
        bot_message = None

output:
[
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

Example 2:
input:  message = 'i wanted to watch movie'
        entity_name = 'movie'
        structured_value = 'inferno'
        structured_value_verification = 0
        fallback_value = None
        bot_message = None

output:
[
  {
    "detection": "structure_value_verified",
    "original_text": "inferno",
    "entity_value": {
      "value": "Inferno"
    }
  }, 
]
```
### Built-in Entities

Following are the list of entities which we have provided for detection purpose:


| entity_name      | type               | description                              |
| ---------------- | ------------------ | ---------------------------------------- |
| restaurant       | text               | Detection of restaurant names from India |
| movie            | text               | Detction of movie names. Mostly, Indian  |
| dish             | text               | Dish detection                           |
| cuisine          | text               | Cuisine detection. For example, pizza, italian, chinese |
| footwear         | text               | Footwear detection. For example, shoes, sandals, |
| date             | date               | Date detection, also detection of additional properties using date_advance |
| time             | time               | Time detection                           |
| city             | city               | City detection                           |
| locality         | location, text     | Detection of indian localities           |
| train_pnr        | pnr                | PNR identification for trains            |
| flight_pnr       | pnr                | PNR identification for flights           |
| number_of_people | number             | Detection of number of people from text  |
| number_of_units  | number             | Detection of numberof units              |
| budget           | budget             | Detection of budget                      |
| shopping_size    | size               | Detects size which are used for shopping. |
| phone_number     | phone_number       | Phone number detection                   |
| brand            | text               | Brand detection of apparels. For example, adidas, nike |
| email            | email              | Email detection                          |

> **NOTE:** To run and check the above entities please have a look at [API call example documentation](api_call.md).
