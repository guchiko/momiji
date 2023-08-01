#!/bin/bash


echo|pwd
echo ##teamcity[buildDetachedFromAgent]
echo '##teamcity[buildDetachedFromAgent]'
cd /home/desu/momiji

until $(curl --output /dev/null --silent --head --fail https://github.com/); do
    printf '.'
    sleep 3
done
nohup python main.py 2>&1 | /usr/bin/logger -t momijitag &
