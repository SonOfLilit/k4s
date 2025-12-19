#!/bin/bash

cd $(dirname "$0")

for container in {health,ping}
do
    docker build -t $container:latest -f Dockerfile.$container .
done
