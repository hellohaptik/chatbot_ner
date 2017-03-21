## Installation and Setup

1. Start a terminal (a shell). You'll perform all subsequent steps in this shell.
2. Install the required build tools

   - Ubuntu:

        ```shell
        $ sudo apt-get update
        $ sudo apt-get install -y python-dev python-pip build-essential curl
        ```

   - Mac OSX (or install Xcode):

     ```shell
     $ xcode-select --install
     ```

     Accept the Xcode license, scroll to bottom and type 'agree' and hit Enter

     ```shell
     $ sudo xcodebuild -license
     ```

     Install pip if you don't have it already

     ```shell
     $ curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | sudo python
     ```


3. Install virtualenvwrapper and setup a virtual python environment

   ```shell
    $ sudo pip install -U virtualenvwrapper
    $ source /usr/local/bin/virtualenvwrapper.sh
    $ mkvirtualenv chatbotnervenv
    $ workon chatbotnervenv
   ```

4. Clone the repository

   $ cd ~/
   ```shell
   $ git clone https://github.com/hellohaptik/chatbot_ner.git
   $ cd chatbot_ner
   ```

5. Install the requirements with pip

   $ pip install -r requirements.txt

6. Install Java and setup Elasticsearch

 You can skip this step if you have separate Elasticsearch instance and don't want to setup one locally

-  Ubuntu:

     ```shell
     $ sudo add-apt-repository -y ppa:webupd8team/java
     $ sudo apt-get update
     $ sudo apt-get -y install oracle-java8-installer
     $ sudo apt install oracle-java8-set-default
     ```

- Mac OSX:

  Please refer to https://docs.oracle.com/javase/8/docs/technotes/guides/install/mac_jdk.html#A1096855 to install Oracle JDK 1.8.x on OSX
  ​     
  Setting up Elasticsearch

 ```shell
 $ mkdir -p ~/chatbot_ner_elasticsearch
 $ cd /tmp/
 $ curl -O https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.4.4/elasticsearch-2.4.4.tar.gz
 $ tar -xzf elasticsearch-2.4.4.tar.gz -C ~/chatbot_ner_elasticsearch/
 $ ~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -d
 ```

 Elasticsearch will be extracted to `~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/`
 ​      

7. Copy config.example to config and configure the settings for datastore

 > **<span style="color:black"> IMPORTANT NOTE:</span> Chatbot NER reads the required connection settings to connect to the DataStore engine from a file called <span style="color:red">`config`</span> located at the root of the repository and exports them in the working environment for further use. In case you don't want to provide this <span style="color:red">`config`</span> file, make sure the required connection settings variables as described in the [DataStore Settings Environment Variables](#dseve) section are somehow set in the environment. Failing to do so will throw a <span style="color:red">`DataStoreSettingsImproperlyConfiguredException`</span> exception while trying to connect to the underlying engine.**

-    Copy `config.example` located in the root of the repository to a separate file named `config`

     ```shell
     $ cd ~/chatbot_ner/
     $ cp config.example config
     ```

- Open and edit the `config` file (with your favorite text editor) and fill in the required settings to connect to the datastore (elasticsearch). See the [DataStore Settings Environment Variables](#dseve) section for details on these variables.

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
