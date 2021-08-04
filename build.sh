#!/bin/bash

# Builds and runs main server image on docker's container

docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)



cd server/

docker build --tag proj_main .

docker ps -a


cd ../

docker build --tag proj_slave .

docker run --name main_server proj_main
