# Named Entity Recognition for chatbots

![chatbotner logo](docs/images/chatbotner_logo.png)

Chatbot NER is an open source framework custom built to supports entity recognition in text messages. After doing
thorough research on existing [NER](https://en.wikipedia.org/wiki/Named-entity_recognition) systems, team at Haptik felt
the strong need of building a framework which is tailored for Conversational AI and also supports Indian languages.
Currently Chatbot-ner supports **English, Hindi, Gujarati, Marathi, Bengali and Tamil** and their ode mixed form.
Currently this framework uses heuristics along with few NLP techniques to extract necessary entities from languages
with sparse data. API structure of Chatbot ner is designed keeping in mind usability for chatbot developers. Team at
Haptik is continuously working towards scaling this framework for **all Indian languages and their respective local
dialects**.

### **Installation**
Detail documentation on how to setup Chatbot NER on your system using docker is available [here](docs/install.md). We
are working on building a pip package for the same.

### **Supported Entities**

| Entity type   | Code reference       | Description                              | example                           | Supported languages - **ISO 639-1** code |
| :------------ | -------------------- | :--------------------------------------- | --------------------------------- | ---------------------------------------- |
| Time          | [TimeDetector](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v2/detectors/temporal/time) | Detect time from given text. | tomorrow morning at 5, कल सुबह ५ बजे, kal subah 5 baje | 'en', 'hi', 'gu', 'bn', 'mr', 'ta' |
| Date          | [DateAdvancedDetector](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v2/detectors/temporal/date) | Detect date from given text | next monday, agle somvar, अगले सोमवार | 'en', 'hi', 'gu', 'bn', 'mr', 'ta' |
| Number        | [TimeDetector](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v2/detectors/numeral/number]) | Detect number and respective units in given text | 50 rs per person, ५ किलो चावल, मुझे एक लीटर ऑइल चाहिए | 'en', 'hi', 'gu', 'bn', 'mr', 'ta' |
| Phone number  | [PhoneDetector](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v2/detectors/pattern/phone_number) | Detect phone number in given text | 9833530536, +91 9833530536, ९८३३४३०५३५ | 'en', 'hi', 'gu', 'bn', 'mr', 'ta' |
| Email         | [EmailDetector](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v1/detectors/pattern/email) | Detect email in text | hello@haptik.co | 'en' |
| Text          | [TextDetector](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v1/detectors/textual/text) | Detects custom entities in text string using full text search in Datastore or based on contextual model| Order me a **pizza**, **मुंबई** में मौसम कैसा है   | Search supported for 'en', 'hi', 'gu', 'bn', 'mr', 'ta', Contextual model supported for 'en' only|
| PNR           | [PNRDetector](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v1/detectors/pattern/pnr) | Detects PNR (serial) codes in given text. | My flight PNR is 4SGX3E | 'en' |

There are other custom detectors such as [city](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v1/detectors/textual/city),
[person name](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v1/detectors/textual/name),
[shopping size](https://github.com/hellohaptik/chatbot_ner/tree/develop/ner_v1/detectors/numeral/size) which are
derived from above mentioned primary detectors but they are supported currently in English only and limited
to Indian users only. We are currently  in process of restructuring them to scale them across languages and geography
and their current versions might be deprecated in future. So **for applications already in production**, we would
recommend you to **use only primary detectors** mentioned in the table above.

### **API structure**
Detail documentation of APIs for all entity types is available [here](docs/api_call.md). Current API structure is
built for ease of accessing it from conversational AI applications. However it can be used for other applications also.

### **Framework Overview**

### **Contribution guidelines**




To know more about our NER repository please go through the following documentations:

1. [Installation and setup](docs/install.md): *Detailed document on how to install and setup the chatbot NER on your system*

2. [CSV file structure and adding/removing entities to DataStore](docs/adding_entities.md): *Document on how to create your own entity and store it to DataStore*

3. [Approach used](docs/approach.md): *Document on the architecture along with different detection logics (entity types) and built-in entities*

4. [API calls](docs/api_call.md): *A brief document on the api calls for different detection logics along with its necessary output*
