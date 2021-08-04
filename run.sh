#!/bin/bash

# runs worker image on docker's container

docker rm worker$1 &> /dev/null

if [ $# -gt 1 ]; then

	if [ $2 = "log" ]; then
		docker run --name worker$1 proj_slave -l
	else
		docker run --name worker$1 proj_slave
	fi
else
	docker run --name worker$1 proj_slave
fi
