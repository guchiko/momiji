#!/bin/sh
echo "hi"
python /usr/app/src/main.py &
echo "NGINX RUN"
/docker-entrypoint.sh nginx -g 'daemon off;'