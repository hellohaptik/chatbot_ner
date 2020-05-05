#!/bin/bash
sudo mkdir -p /opt/models_crf
sudo chown ubuntu:ubuntu /opt/models_crf
aws s3 cp s3://prodner/models/ /opt/models_crf/ --recursive --region=ap-south-1
