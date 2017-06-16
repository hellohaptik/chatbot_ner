Following are the steps to create the Docker image and run NER via Docker

Install Docker 
`wget get.docker.com` 
`bash index.html`
Add your current user to Docker group:
`sudo usermod -aG docker $USER`

Once the above is setup, to run Chatbot_NER via Docker use the following command:

`docker pull haptik/chatbot_ner docker run -itd -p 80:8081 --name ner haptik/chatbot_ner`

Now, on your local machine curl the chatbot api as shown shown below, host can be your local machine or a server IP on which you have been running docker on.

To Create Custom Docker Images

`git clone https://github.com/hellohaptik/chatbot_ner.git`
Go into the cloned repo:
`cd chatbot_ner`
Now, go into the Docker folder:
`cd docker`
Build Docker Image using the below command:
`docker build -t ner_image .`
Now, your image is made.
To list images use:
`docker images` (list the images)
Now, use the below command to use run Docker container
`docker run -itd -p 80:8081 --name ner ner_image`

To get into the container to make any tweaks etc. use the following command:
`docker exec -it ner bash`
The above will give you bash shell access to the container. 

To access chatbot_ner:
`curl localhost:80/YOUR_QUERY`



