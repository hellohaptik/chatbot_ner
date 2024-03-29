# Setup Chatbot NER with Docker
Following are the steps to create the Docker image and run NER with Docker.

1. **Install Docker & Docker Compose**

   - Ubuntu:

      ```shell
      wget get.docker.com
      bash index.html
      # add your current user to Docker group
      sudo usermod -aG docker $USER
      ```

      If the above does not work try:

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
      sudo usermod -a -G ubuntu   (change username as per need)
      ````

      Docker Compose
      ```shell
      sudo curl -L "https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      sudo chmod +x /usr/local/bin/docker-compose
      ```
   - MacOS:

     Please follow the installation document: https://docs.docker.com/docker-for-mac/install/

2. **Cloning chatbot_ner :**
  ```bash
  git clone https://github.com/hellohaptik/chatbot_ner.git
  cd chatbot_ner
  # copying dev setup files
  cp ./dev_docker/* ./
  ```

3. **Seting up configuration:**
  Setting up configuration: These setups should be in the parent level directory. Which means inside ~/chatbot_ner/
  - Copy file `.env.example` to `.env` and modify it based on requirements.
    - **NOTE** : For updating the .env file Haptik employee can refer to internal notion doc [here](https://www.notion.so/hellohaptik/Alternate-dev-setup-for-NER-env-file-Entity-syncing-7f47ee691aed41c3b7025f2b1976bd14). If you don't have access to the notion doc, contact your manager or someone from the ML team.
  - In `.env` file you should change the `SECRET_KEY`.
  - Update permission for `entrypoint.sh` file
  ```bash
  sudo chmod 777 entrypoint.sh
  ```
4. **Bring up chatbot_ner:**
  - Now its time to build the containers and bring them up.
  ```bash
  docker-compose up --build -d
  ```
  - Verify if containers are up by docker-compose ps. Keep monitoring for about 1 minute to check if the elasticsearch container is being restarted.

  - In case the elasticsearch container keeps restarting. There are some permission issues with the local folder used by the elasticsearch container. There should be a folder created by elasticsearch with path ~/chatbot_ner/dbdata/esdata/v1.

  - Now bring down the containers and Provide required permission to the above folder. Then bring up the containers.
  ```bash
  cd ~/chatbot_ner
  # stop containers
  docker-compose down
  # verify containers are stopped
  docker-compose ps
  # give permission to folder
  sudo chmod -r 777 ./dbdata/esdata/v1
  # start the containers
  docker-compose up --build -d
  ```

The above will also mount the local repo root directory inside the containers /app directory. Please wait 5 seconds to run the first curl or do an API call to chatbot_ner.
The above will also mount local repo root directory inside the containers /app directory.
Please wait 5 seconds to run the first curl or do an API call to chatbot_ner.
   > **NOTE**: make sure that nothing is running on port 8081 on your server or your local environment.
     If anything is running on port 8081, you can stop it by running the following command
   >
   > `sudo lsof -t -i tcp:8081 -s tcp:listen | sudo xargs kill`

   > We have mapped port 80 of the docker container to port 8081 of your machine.
     Now, on your local machine curl the chatbot api as shown shown below,
     host can be your local machine or a server IP on which you have been running docker on.

   > Port mapping can be changed in docker-compose yml

**Container commands:**

   ```shell
cd ~/chatbot_ner/docker  # (all compose commands from docker directory of repo)
docker-compose ps or docker ps # (shows list of running container)
docker exec -it container-name bash  # (login to container shell)
docker-compose down # (to kill containers)
docker-compose restart # (to restart containers, probably when you make code changes)
   ```
**Check logs**
   ```shell
docker logs -f docker_chatbot-ner_1
   ```
   ```shell
cd ~/chatbot_ner/logs
tail -f *.log
   ```

>  `docker_chatbot-ner_1` is the docker container name
>
>   `LOG_LEVEL` can be changed in compose or chatbot_ner/config.py

**Example API call to test**

 Following is an example API call to test our service on your local system/server:

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

- You can also have a look at our [API call document](/docs/api_call.md) to test and use different NER functionalities.
- To access GUI, go to http://localhost:8081/gui/ or http://host-ip/gui/



**IMPORTANT NOTE:** If you bring down the container and bring it up again, `datastore_setup.py` will run again. If you added some data and do not want it to get reset on ELASTICSEARCH, comment out DataStore section in `datastore_setup.py`

## To Create Custom Docker Images

If you want to create a custom Docker image execute the following commands after making changes to Dockerfile and scripts.

```shell
$ cd chatbot_ner
$ cd docker
$ sudo docker build -t ner_image .
$ sudo docker run -itd -p 8081:80 --name ner ner_image
```

## Delete Docker Data

```shell
$ sudo docker rm -f ner
$ sudo docker rmi -f mlhaptik/chatbot_ner
$ sudo apt-get remove docker
```
