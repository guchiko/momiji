#!/bin/bash


echo|pwd
cd /home/desu/momiji

until $(curl --output /dev/null --silent --head --fail https://github.com/); do
    printf '.'
    sleep 3
done
python main.py 2>&1 | /usr/bin/logger -t momijitag
