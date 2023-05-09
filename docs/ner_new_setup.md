# Alternate Setup for Chatbot ner (Only for Dev purpose with Elasticserach)
Below are steps required for setting up `chatbot_ner` on dev system. Assuming NER setup is at path `~/chatbot_ner`

**NOTE** : This setup is tested on development environment only therefore its working on other environments is not guareented.

## Cloning chatbot_ner
If you are doing a new setup.
```bash
git clone https://github.com/hellohaptik/chatbot_ner.git
cd chatbot_ner
```

## Stop existing docket setup
In case you are working with existing docker setup and modify it to new one. Then you will have to stop existing NER docker setup.
- Switch to directory `docker/` and stop any existing docker setup running through that directory.

```bash
cd ~/chatbot_ner/docker
docker-compose down
```

- Copy the files from directory `dev_setup_examples` to parent directory. This directory contain examples files which can be configured and used in our new setup.
```bash
cd ~/chatbot_ner/
cp -r ./dev_setup_examples/*  ./
```

## Seting up configuration
These setups should be in parent level directory. Which means inside `~/chatbot_ner/`
- Copy file `.env.example` to `.env` and modify it based on requirements. For updating .env file Haptik employee can refer to internal notion doc [here](https://www.notion.so/hellohaptik/Alternate-dev-setup-for-NER-env-file-Entity-syncing-7f47ee691aed41c3b7025f2b1976bd14) . If you don't have access to the notion doc, contact with your manager or someone from ML team.
- Update permission for `entrypoint.sh` file
```bash
sudo chmod 777 entrypoint.sh
```

## Running up the container
- Now its time to build the containers and bring them up.
```bash
docker-compose up --build -d
```
- Verify if containers are up by `docker-compose ps`. Keep monitoring for about 1 minutes to check if elasticsearch container is being restarted.

- In case elasticsearch container keep restarting. There are some permission issue with the local folder used by elasticsearch container.
There should a folder created by elasticsearch with path `~/chatbot_ner/dbdata/esdata/v1`.
- Now bring down the containers and Provide required permission to above folder. Then bring up the containers.
```bash
cd ~/chatbot_ner

# stop containers
docker-compose down

# verify containers are stopped
docker-compose ps

# give permission to folder
sudo chmod -r 777 ./dbdata/esdata/v1

# start the containers
docker-compose up -d
```

### Some points to help in case any issue occurs
- check `docker-compose.yml` and make port used there is not already being used by any other service.
- In case any required .env key is missing or setup is not configured propery, containers might restart again and again. Therefore it is advice to keep look on docker logs to check for such errors.


## Continue futher setup from Install.md
Now you may need to test the REST API for NER for which refer to section **Testing NER API** in [Install.md](./install.md#testing-ner-api)