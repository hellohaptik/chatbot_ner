# Named Entity Recognition for chatbots

![chatbotner logo](docs/images/chatbotner_logo.png)

Chatbot NER is an open source framework custom built to supports entity recognition in text messages. After doing
thorough research on existing [NER](https://en.wikipedia.org/wiki/Named-entity_recognition) systems, team at Haptik felt
the strong need of building a framework which is tailored for Conversational AI and also supports Indian languages.
Currently Chatbot-ner supports **English, Hindi, Gujarati, Marathi, Bengali and Tamil**. Currently this framework uses
heuristics along with few NLP techniques to extract necessary entities from languages with sparse data. API structure
of Chatbot ner is designed keeping in mind usability for chatbot developers. Team at Haptik is continuously working
towards scaling this framework for **all Indian languages and their respective local dialects**.

### **Installation**
Detail documentation on how to setup Chatbot NER on your system using docker is available [here](docs/install.md). We
are working on building a pip package for the same.

### **API structure**
Detecil documentation of APIs for all entity types is available [here](docs/api_call.md). Current API structure is
built for ease of accessing it from conversational AI applications. However it can be used for other applications also.

### **Framework Overview**




To know more about our NER repository please go through the following documentations:

1. [Installation and setup](docs/install.md): *Detailed document on how to install and setup the chatbot NER on your system*

2. [CSV file structure and adding/removing entities to DataStore](docs/adding_entities.md): *Document on how to create your own entity and store it to DataStore*

3. [Approach used](docs/approach.md): *Document on the architecture along with different detection logics (entity types) and built-in entities*

4. [API calls](docs/api_call.md): *A brief document on the api calls for different detection logics along with its necessary output*
