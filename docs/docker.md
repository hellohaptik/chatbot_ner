# Setup of Chatbot NER via. Docker

Following are the steps to create the Docker image and run NER via Docker.

1. Install Docker 

   - Ubuntu:

     ```shell
     $ wget get.docker.com
     $ bash index.html
     # add your current user to Docker group
     $ sudo usermod -aG docker $USER
     ```

   - Mac OSX:

     Follow the installation document: https://docs.docker.com/docker-for-mac/install/

2. Pull and run Chatbot NER via Docker use the following command:

   ```shell
   $ sudo docker pull mlhaptik/chatbot_ner
   ```

   > **NOTE**: make sure that nothing is running on port 80 on your server or your local environment. If anything is running on port 80 run the following command
   >
   > `sudo lsof -t -i tcp:80 -s tcp:listen | sudo xargs kill`

   ```shell
   $ sudo docker run -itd -p 80:80 --name ner mlhaptik/chatbot_ner
   ```

   > We have mapped port 80 of the docker container to  port 80 of your machine. Now, on your local machine curl the chatbot api as shown shown below, host can be your local machine or a server IP on which you have been running docker on.

3. To get inside container execute the following:

   ```shell
   $ sudo docker exec -it ner bash
   ```

4. Start the Chatbot NER inside the container

   ```shell
   $ cd ~/chatbot_ner
   $ ./start_server.sh &
   ```

   ​

   Following is the API call to test our service on your local system:

   ```python
   entities = ['date','time','restaurant']
   message = "Reserve me a table today at 6:30pm at Mainland China and on Monday at 7:00pm at Barbeque Nation" 
   ```

   ```shell
   URL='localhost'
   PORT=80
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

   **NOTE:**

   - You can also have a look at our [API call document](/docs/api_call.md) to test and use different NER functionalities.
   - To access GUI, go to http://localhost:80/gui/ 

   ​


## To Create Custom Docker Images

If you want to create a custom Docker image execute the following commands after making changes to Dockerfile and scripts.

```shell
$ cd chatbot_ner
$ cd docker
$ sudo docker build -t ner_image .
$ sudo docker run -itd -p 80:80 --name ner ner_image
```

## Delete Docker Data

```shell
$ sudo docker rm -f ner
$ sudo docker rmi -f mlhaptik/chatbot_ner
$ sudo apt-get remove docker
```

