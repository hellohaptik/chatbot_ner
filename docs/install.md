## Installation and Setup

1. Start a terminal (a shell). You'll perform all subsequent steps in this shell.
2. Install the required build tools

   - Ubuntu:

     ```shell
        $ sudo apt-get update
        $ sudo apt-get install -y python-dev python-pip build-essential curl
     ```

   - Mac OSX:

     Install pip if you don't have it already

     ```shell
     $ sudo easy_install pip
     ```


3.  Install virtualenvwrapper and setup a virtual python environment

    ```shell
     $ sudo pip install -U virtualenvwrapper
     $ source /usr/local/bin/virtualenvwrapper.sh
     $ mkvirtualenv chatbotnervenv
     $ workon chatbotnervenv
    ```

4.  Clone the repository

    ```shell
    $ cd ~/
    $ git clone https://github.com/hellohaptik/chatbot_ner.git
    $ cd chatbot_ner
    ```

5.  Install the requirements with pip

    ```shell
    $ pip install -r requirements.txt
    ```

6.  Install Java and setup Elasticsearch

     You can skip this step if you have separate Elasticsearch instance and don't want to setup one locally

    -  Ubuntu:

       ```shell
        $ sudo add-apt-repository -y ppa:webupd8team/java
        $ sudo apt-get update
        $ sudo apt-get -y install oracle-java8-installer
        $ sudo apt install oracle-java8-set-default
       ```

    -  Mac OSX:

         Please refer to https://docs.oracle.com/javase/8/docs/technotes/guides/install/mac_jdk.html#A1096855 to install Oracle JDK 1.8.x on OSX

    Setting up Elasticsearch

    ```shell
    $ mkdir -p ~/chatbot_ner_elasticsearch
    $ cd /tmp/
    $ curl -O https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.4.4/elasticsearch-2.4.4.tar.gz
    $ tar -xzf elasticsearch-2.4.4.tar.gz -C ~/chatbot_ner_elasticsearch/
    $ ~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -d
    ```

     Elasticsearch will be extracted to `~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/`


7. Copy config.example to config and configure the settings for datastore

 > **<span style="color:black"> IMPORTANT NOTE:</span> Chatbot NER reads the required connection settings to connect to the DataStore engine from a file called <span style="color:red">`config`</span> located at the root of the repository and exports them in the working environment for further use. In case you don't want to provide this <span style="color:red">`config`</span> file, make sure the required connection settings variables as described in the [DataStore Settings Environment Variables](/docs/datastore_variables.md) section are somehow set in the environment. Failing to do so will throw a <span style="color:red">`DataStoreSettingsImproperlyConfiguredException`</span> exception while trying to connect to the underlying engine.**

-    Copy `config.example` located in the root of the repository to a separate file named `config`

     ```shell
     $ cd ~/chatbot_ner/
     $ cp config.example config
     ```

-    Open and edit the `config` file (with your favorite text editor) and fill in the required settings to connect to the datastore (elasticsearch). See the [DataStore Settings Environment Variables](/docs/datastore_variables.md) section for details on these variables.

8. Run initial_setup.py to install required nltk corpora and populate DataStore with data from csv files present at `data/entity_data/`.


```shell
   $ python initial_setup.py
```

You can add your own entities using such csv files. See [CSV file structure and adding new entities to DataStore](/docs/adding_entities.md) section for more details.


​        
## Starting the NER

```shell
   $ ./start_server.sh
```

   Or if you wish to run it in background

```shell
   $ ./start_server.sh &
```

Following is the API call to test our service:

```python
entities = ['date','time','restaurant']
message = "Reserve me a table today at 6:30pm at Mainland China and on Monday at 7:00pm at Barbeque Nation" 
```

```shell
URL='localhost'
PORT=8081
curl -i 'http://'$URL':'$PORT'/v1/ner/?entities=\[%22date%22,%22time%22,%22restaurant%22\]&message=Reserve%20me%20a%20table%20today%20at%206:30pm%20at%20Mainland%20China%20and%20on%20Monday%20at%207:00pm%20at%20Barbeque%20Nation'
```

Output should be:

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

You can also have a look at our [API call document](/docs/api_call.md) to test and use different NER functionalities.
