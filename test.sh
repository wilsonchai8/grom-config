#!/bin/bash

image=grom-config:$1
name=grom-config
#docker pull $image
docker rm -f $name
docker run -d --restart=always  --name=$name\
    -v /home/wilson/workspace/grom/grom-config/app.conf:/opt/grom-config/app.conf \
    -v /home/wilson/workspace/grom/grom-config/src:/opt/grom-config/src \
    -p 10002:10002 \
    $image 
