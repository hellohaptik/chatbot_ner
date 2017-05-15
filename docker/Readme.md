Following are the steps to create the Docker image and run NER via Docker

Install Docker 
wget get.docker.com  && bash index.html

To run Chatbot_NER via Docker 

docker pull haptik/chatbot_ner
docker run -itd -p 80:8081 --name ner haptik/chatbot_ner
Now, on your local machine curl the chatbot api as shown shown below, host can be your local machine or a server IP on which you have been running docker on.
.....
....

To Create Docker Image 
1. This repo should be cloned
2. Go into the chatbot_ner cloned repo
3. cd docker 
4. vim Dockerfile
   Uncomment lines if you want to run via virtualenv support, else build the Dockerfile as shown in the next step as it is.
5. docker build -t ner_image .
6. Your image is made.
7. docker images (list the images)
6. run the image: 
   docker run -itd -p 80:8081 --name ner ner_image
