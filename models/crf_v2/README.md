## CONDITIONAL RANDOM FIELDS


### A. INTRODUCTION

Conditional random fields (CRFs) are a class of statistical modeling method often applied in pattern recognition and machine learning and used for structured prediction. CRFs fall into the sequence modeling family. Whereas a discrete classifier predicts a label for a single sample without considering "neighboring" samples, a CRF can take context into account; e.g., the linear chain CRF (which is popular in natural language processing) predicts sequences of labels for sequences of input samples.


CRFs are a type of discriminative undirected probabilistic graphical model. They are used to encode known relationships between observations and construct consistent interpretations and are often used for labeling or parsing of sequential data, such as natural language processing or biological sequences and in computer vision. Specifically, CRFs find applications in POS Tagging, shallow parsing, named entity recognition, gene finding and peptide critical functional region finding, among other tasks, being an alternative to the related hidden Markov models (HMMs). In computer vision, CRFs are often used for object recognition and image segmentation.

We have implemented a CRF model for Named Entity Recognition. In addition to commonly used primitive features we have incorporated glove embeddings in order to add semantic knowledge to the Entity Recognition algorithm.

Since the CRF model is used to detect named-entities we thus have assigned CRF Entities are assigned **text** type

### B. SETUP

**1. Word Embeddings**

The module we have deployed incorporates glove embeddings inorder to incorporate semantic meaning to the algorithm.

```python
import os
import wget
import zipfile
import gensim
from gensim.test.utils import datapath, get_tmpfile
from gensim.models import KeyedVectors
from gensim.scripts.glove2word2vec import glove2word2vec
import pickle

wget.download(url='http://nlp.stanford.edu/data/glove.twitter.27B.zip')

zip_ref = zipfile.ZipFile('glove.twitter.27B.zip', 'r')
zip_ref.extract(member='glove.twitter.27B.25d.txt')
os.remove('glove.twitter.27B.zip')

glove2word2vec('glove.twitter.27B.25d.txt', 'test_word2vec_new_nearby.txt')
word_vectors = KeyedVectors.load_word2vec_format('test_word2vec_new_nearby.txt')

os.remove('glove.twitter.27B.25d.txt')
os.remove('test_word2vec_new_nearby.txt')
file_handler = open('glove_vocab', 'wb')
pickle.dump(obj=word_vectors.wv.index2word,file=file_handler, protocol=2)
file_handler = open('glove_vectors', 'wb')
pickle.dump(obj=word_vectors.wv.vectors, file=file_handler, protocol=2)

if not os.path.exists('/app/models_crf/'):
    os.makedirs('/app/models_crf/')

```
    
**2. Environment Keys**

**ADD** the following keys to the environment
   	  
```bash 
MODELS_PATH=/app/models_crf
EMBEDDINGS_PATH_VOCAB=/app/glove_vocab
EMBEDDINGS_PATH_VECTORS=/app/glove_vectors
```
Add the above specified dir/files to .gitignore    

### C. TRAINING


**1. Input Training Data**

Generate training data for CRF model in the CSV format. The csv files should consists of the sentences and their corresponding entities on which the model has to be trained. This CSV is just for convenience. Direct sentence_list and entity_list can be provided as input.

-	**sentence_list**
	
    The columns consists of texts (text patterns) on which the module needs to be trained. The model  learns to recognize the the entities present in the sentences in a supervised fashion.


-	**entity_list**
	
    The column consists of the list of entities present in the corresponding sentences.`

**Example**

| sentence_list                            | entity_list                    |
| ---------------------------------------- | ------------------------------ |
| My name is Pratik Jayarao                | ["Pratik Jayarao"]             |
| My name is Pratik                        | ["Pratik"]                     |
| My name is Pratik Sridatt Jayarao        | ["Pratik Sridatt Jayarao"]     |
| My name is Pratik and this is my friend Hardik | ["Pratik", "Hardik"]           |
| People call me Harsh Shah                | ["Harsh Shah"]                 |
| Chirag Jain is my name and I live in India | ["Chirag Jain"]                |
| Myself Aman Srivastava and I Engineer    | ["Aman Srivastava"]            |
| People call me Yash Doshi and my friend Sagar Dedhia | ["Yash Doshi", "Sagar Dedhia"] |
| Hi, how are you doing?                   | []                             

**Note** Convert CSV file into sentence_list and entity_list utilizing the following code
```python
from models.crf_v2.crf_train import CrfTrain
import ast
import pandas as pd

csv_path = '/app/crf_chat.csv'  #  The path where the csv file is stored.

data = pd.read_csv(csv_path, encoding='utf-8') #  Load the csv file into a pandas DataFrame
sentence_list = list(data['sentence_list']) 
entity_list = list(data['entity_list'].apply(lambda x: ast.literal_eval(x)))

```

**2. Preprocess Data**

The module is used to take input as the sentence_list and entity_list and converts it to features for training the Crf Model.

-	**Tokenization and Label Generation**
	
    This module is used to tokenize and generate labels according to the IOB standards of Named Entity Recognition (NER)
    	
       ```python
       from models.crf_v2.crf_preprocess_data import CrfPreprocessData
      sentence_list =['book a flight from Mumbai to Delhi', 'Book a flight to Pune']
       entity_list = [['Mumbai', 'Delhi'], ['Pune']]
	   docs = CrfPreprocessData.pre_process_text(sentence_list, entity_list)
       print(docs)

       >>> {'labels': [['O', 'O', 'O', 'O', 'B', 'O', 'B'], ['O', 'O', 'O',
       >>> 'O', 'B']],
       >>> 'sentence_list': [['book', 'a', 'flight', 'from', 
       >>> 'Mumbai','to', 'Delhi'], ['Book', 'a', 'flight', 'to', 'Pune']]}
	```

-	**Parts Of Speech Tagging**

	This module is used to tag the parts of speech for the tokenized sentences
	```python
    from models.crf_v2.crf_preprocess_data import CrfPreprocessData
    docs = CrfPreprocessData.pos_tag(docs)
    print(docs)

    >>> {'labels': [['O', 'O', 'O', 'O', 'B', 'O', 'B'], 
    >>> ['O', 'O', 'O', 'O', 'B']],
    >>> 'pos_tags': [['NN', 'DT', 'NN', 'IN', 'NNP', 'TO', 'VB'], 
    >>> ['VB', 'DT', 'NN', 'TO', 'VB']],
    >>> 'sentence_list': [['book', 'a', 'flight', 'from', 
    >>> 'Mumbai', 'to', 'Delhi'],['Book', 'a', 'flight', 'to', 'Pune']}
	```

- 	**Load Word Embeddings**
	
	This module is used to load the word embeddings into the memory
        
    ```python
    from models.crf_v2.load_word_embeddings import LoadWordEmbeddings
    word_embeddings = LoadWordEmbeddings()
    vocab = word_embeddings.vocab
    word_vectors = word_embeddings.word_vectors
    ```

-	**Assign Word Embeddings**
	
    This module is used to load the word embeddings from the local disk and then each token is assigned a its coressponsding word embedding
    
    ```python
    from models.crf_v2.crf_preprocess_data import CrfPreprocessData
    docs['word_embeddings'] = 
    [CrfPreprocessData.word_embeddings(processed_pos_tag_data=each,
    vocab=vocab, word_vectors=word_vectors) 
    for each in docs[SENTENCE_LIST]]
	```
    
-	**Generate Feature From Data**
    
    This module is to generate feature for each token which acts as the input features for the CRF Model
    
    -	**Window Size**
	
		We consider a window of two tokens in the forward and the backward direction for each token at a given time step.

		**Example**

		1. My name |_is Pratik **Jayarao** and this_| is my friend Hardik Patel.
		2. I want to |**travel from **Mumbai** to Delhi**|

	-	**Token features**
	
		Each token present in the window is converted to the following features as an input

		1. **lower**     
		
        	The token is casted to the lower case.
		
		2. **isupper**  
		
	        Flag to check if the complete token is in upper case
		
		3. **istitle**
		
            Flag to check if the first letter of the token is capitalized
		
		4. **isdigit**   
		
        	Flag to check if the token is a digit
		
		5. **pos_tag**  
	
        	Part of speech tag for the given token
		
		6. **word_embeddings** 

		Word Vectors associated with each token

    ```python
    from models.crf_v2.crf_preprocess_data import CrfPreprocessData
    features = CrfPreprocessData.extract_crf_features(docs)
    labels = docs['labels']
    ```
3. **Train Crf Model**

	This module takes input as the features and the and labels obtained from the preprocessing module and trains a CRF model on it. The module saves this model locally and this path is then returned.
    
	**Model Cofigurations**
	-	C1 - L1 Regularization constant 
	-	C2 - L2 Regularization constant
	-	Max Iterations - Max number of iterations to be executed
    
	```python
	from models.crf_v2.crf_train import CrfTrain
	
	crf_train = CrfTrain(entity_name='crf_chat')
	model_path = crf_train.train_crf_model(x=features, y=labels, c1=0, c2=0,
    max_iterations=1000)

	print(model_path)

	>>>'/app/models_crf/crf_chat' 
	```

4. **Training Example**
    
	```python
    from models.crf_v2.crf_train import CrfTrain
    import ast
    import pandas as pd

    entity_name = 'crf_chat' #  The name of entity which will be reflected in the model and is the primary identifier of the entity.
    csv_path = '/app/crf_chat.csv'  #  The path where the csv file is stored.

    data = pd.read_csv(csv_path, encoding='utf-8') #  Load the csv file into a pandas DataFrame
    sentence_list = list(data['sentence_list']) 
    entity_list = list(data['entity_list'].apply(lambda x: ast.literal_eval(x)))

    crf_model = CrfTrain(entity_name=entity_name) #  Initialize the Crf Model
    model_path = crf_model.train_crf_model_from_list(sentence_list=sentence_list, entity_list=entity_list)

    print(model_path)

    >>>'/app/models_crf/crf_chat' 
	```

### D. CRF ENTITY DETECTION (Standalone)

The mdoule can be used to detect entities utilizing the previously trained CRF model. This module takes input as the entity name and the text from which the entity has to be extracted.

1. **Load Model**

	The crf model corresponding to the entity is loaded from the local disk into the memory and the tagger is initialized. This module is a Singelton class and hence the model if once loaded remaines in the memory.
    
2. **Extract Entity**

	This module is responsible to tag the entities from text and return the detected subtexts.
    
```python
from models.crf_v2.crf_detect_entity import CrfDetection
crf_detection = CrfDetection(entity_name='crf_chat')
detected_text = crf_detection.detect_entity(text='People call me Aman Shah and my friend Krupal Modi')
print(detected_text)
>>> ['Aman Shah', 'Krupal Modi']
```
### E. CRF-TEXT ENTITY DETECTION (Combined Module)

This module is used to run the previously trained CRF model alongside the tradional text entity detection (detection accomplished from datastore). This module takes input as the entity name and returns a combined result using both CRF Detection and Text Entity Detection.

1. **CRF Standalone Detection**

	The CRF Standalone Detection is triggered. The result i.e the list of entities detected from the CRF is returned.
    
2. **Text Entity Detection**

	This module is used to detect entities leveraging the Text entity fucntionality. This module returns the entity_value and the original_text.

3. **Verification Source**
	
	This module is responsible to assign the source (CRF / Datastore) from which the entity is detected.
    
4. **Ensemble Results**

	This module is responsible to combine the results detected from the Datastore and the CRF Model. The Datastore value is given higher priority. If the same entity is detected by the CRF model and the Datastore then the entity value is resolved to the entity value returned by the Datastore Module

```python
from ner_v1.detectors.textual.text.text_detection_model import TextModelDetector
text_model_detector = TextModelDetector(entity_name='crf_chat', live_crf_model_path='/app/models_crf/crf_chat')
output = text_model_detector.detect(message='my name is harsh')
print(output)
>>> [{'detection': 'message',
  	'entity_value': {'crf_model_verified': True,
    'datastore_verified': False,
   	'value': 'harsh'},
  	'language': 'en',
  	'original_text': 'harsh'}]

```

### F. PYTHON API DOCUMENTATION



**1. Training**
  
```python

import pandas as pd
import json
import requests
import ast

def convert_data_to_json(csv_path, entity_name):
    """
    This method is used to convert the CSV file into the appropriate json which will be
    consumed by the Chatbot Ner docker. 
    
    Args:
	    csv_path (str): The local path where the training data is stored
    	entity_name (str): Name associated with the entity (will be added in the model
    	path)
    	language_script (str): The script of the training data
    
    Returns:
    	external_api_data (str): json dump of the transformed training data dictionary
    	which will be used to train the crf model on the training data
    """
    
    data = pd.read_csv(csv_path, encoding='utf-8')

    sentence_list = list(data['sentence_list'])
    entity_list = list(data['entity_list'].apply(lambda x: ast.literal_eval(x)))

    external_api_data = json.dumps({
        'entity_name': entity_name,
        'sentence_list': sentence_list,
        'entity_list': entity_list,
    })
    return external_api_data
    
def train_crf_model(external_api_data, chatbot_ner_url, http_timeout):
  """
  This method is used to train the crf model on the transformed (convert_data_to_json)
  training data.
  
  Args:
  	external_api_data (str): json dump of the transformed training data dictionary
  	which will be used to train the crf model on the training data (output of
  	convert_data_to_json)
  	chatbot_ner_url (str): The base chatbot ner url for the docker.
  	http_timeout (int): The time out for the api call to Chatbot Ner to train the model
  
  Returns:
  	live_crf_model_path (str): The path where the trained crf model is stored.
  """
 
  url = chatbot_ner_url + '/entities/train_crf_model'
  params = {'external_api_data': external_api_data}
  response = requests.post(url, data=params, timeout=http_timeout)
  response_body = json.loads(response.text)
  live_crf_model_path = response_body.get('result').get('live_crf_model_path')
  return live_crf_model_path
  

#  CONSTANTS
CHATBOT_NER_SCHEMA = 'http://'
CHATBOT_NER_HOST = 'localhost'
CHATBOT_NER_PORT = '8081'
CHATBOT_NER_URL = CHATBOT_NER_SCHEMA + CHATBOT_NER_HOST + ':' + CHATBOT_NER_PORT
HTTP_TIMEOUT = 100
CSV_PATH = "/home/ubuntu/crf_chat.csv"
ENTITY_NAME = 'crf_chat'


external_api_data= convert_data_to_json(csv_path=CSV_PATH, entity_name=ENTITY_NAME) 

live_crf_model_path = train_crf_model(external_api_data=external_api_data, chatbot_ner_url=CHATBOT_NER_URL, http_timeout=HTTP_TIMEOUT)

print(live_crf_model_path)
>>> u'/app/models_crf/crf_chat'

```
**Note** _Save the **live_crf_model_path**_

**2. Detection**
This code can be used to detect the entities from the given text
```python
from ner_v1.detectors.textual.text.text_detection_model import TextModelDetector
text_model_detector = TextModelDetector(entity_name='crf_chat', live_crf_model_path=live_crf_model_path)
output = text_model_detector.detect(message='my name is harsh')
print(output)
>>> [{'detection': 'message',
  	'entity_value': {'crf_model_verified': True,
    'datastore_verified': False,
   	'value': 'harsh'},
  	'language': 'en',
  	'original_text': 'harsh'}]

```
