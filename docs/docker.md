# Setup of Chatbot NER via. Docker
> Note: The docker setup creates no user and uses elasticsearch 2.x in root mode,
> the support for which has been removed since elasticsearch 5.x.
> The code in develop has been changed to support 5.x+ but the docker file has not been updated yet

Following are the steps to create the Docker image and run NER via Docker.

1. Install Docker & Docker Compose

   - Ubuntu:

     ```shell
     $ wget get.docker.com
     $ bash index.html
     # add your current user to Docker group
     $ sudo usermod -aG docker $USER
     ```
   - If the above does not work try:
     ````shell
     sudo apt-get -y \
     update
     sudo apt-get install \
     apt-transport-https \
     ca-certificates \
     curl \
     software-properties-common
     
     curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
     
     sudo apt-key fingerprint 0EBFCD88
     
     sudo add-apt-repository \
     "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) \
     Stable"
     
     sudo apt-get update
     sudo apt-get install docker-ce
     ````
    
   - Docker Compose
     ```shell
      sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
      sudo chmod +x /usr/local/bin/docker-compose

     ``` 


   - Mac OSX:

     Follow the installation document: https://docs.docker.com/docker-for-mac/install/
     



Bring up chatbot_ner:
      
    ```shell
       cd chatbot_ner 
       cd docker
       docker-compose up -d 
    ```

The above will also mount local repo root directory inside the containers /app directory

   > **NOTE**: make sure that nothing is running on port 80 on your server or your local environment. If anything is running on port 80 run the following command
   >
   > `sudo lsof -t -i tcp:80 -s tcp:listen | sudo xargs kill`
   
   > We have mapped port 80 of the docker container to  port 80 of your machine. Now, on your local machine curl the chatbot api as shown shown below, host can be your local machine or a server IP on which you have been running docker on.
   
   > Port mapping can be changed in docker-compose yml 

Container commands:

   ```shell
   $ cd ~/chatbot_ner/docker  (all compose commands from docker directory of repo)
   $ docker-compose ps or docker ps (shows list of running container)
   $ sudo docker exec -it (container-name) bash
   ```
   Check logs 
   ```shell
   $ docker logs -f (container-name)
   ```
   ​-f is for tail
   
   Following is the API call to test our service on your local system/server:

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
        "tag": "reserve me a table __date__ at __time__ at mainland china and on __date__ at __time__ at barbeque nation",
        "entity_data": {
          "date": [
            {
              "detection": "message",
              "original_text": "monday",
              "entity_value": {
                "end_range": false,
                "from": false,
                "normal": true,
                "value": {
                  "mm": 8,
                  "yy": 2017,
                  "dd": 28,
                  "type": "day_within_one_week"
                },
                "to": false,
                "start_range": false
              }
            },
            {
              "detection": "message",
              "original_text": "today",
              "entity_value": {
                "end_range": false,
                "from": false,
                "normal": true,
                "value": {
                  "mm": 8,
                  "yy": 2017,
                  "dd": 23,
                  "type": "today"
                },
                "to": false,
                "start_range": false
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
   - To access GUI, go to http://localhost:80/gui/ or http://host-ip/gui/

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

