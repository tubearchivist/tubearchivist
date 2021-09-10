#!/bin/bash

# deploy all needed project files to different servers:
# test for local vm for testing
# blackhole for local production
# docker to publish

set -e

function sync_blackhole {

    # docker commands need sudo
    host="blackhole.local"

    read -sp 'Password: ' remote_pw
    export PASS=$remote_pw
    
    rsync -a --progress --delete-after \
        --exclude ".git" \
        --exclude ".gitignore" \
        --exclude "**/cache" \
        --exclude "**/__pycache__/" \
        --exclude "db.sqlite3" \
        . -e ssh "$host":tubearchivist

    echo "$PASS" | ssh "$host" 'sudo -S docker build -t bbilly1/tubearchivist:latest tubearchivist 2>/dev/null'
    echo "$PASS" | ssh "$host" 'sudo -S docker-compose up -d 2>/dev/null'

}

function sync_test {

    # docker commands don't need sudo in testing vm
    host="tubearchivist.local"

    rsync -a --progress --delete-after \
        --exclude ".git" \
        --exclude ".gitignore" \
        --exclude "**/cache" \
        --exclude "**/__pycache__/" \
        --exclude "db.sqlite3" \
        . -e ssh "$host":tubearchivist

    rsync -r --progress --delete docker-compose.yml -e ssh "$host":docker

    ssh "$host" 'docker build -t bbilly1/tubearchivist:latest tubearchivist'
    ssh "$host" 'docker-compose -f docker/docker-compose.yml up -d'

    ssh "$host" 'docker cp tubearchivist/tubearchivist/testing.sh tubearchivist:/app/testing.sh'
    ssh "$host" 'docker exec tubearchivist chmod +x /app/testing.sh'

}


function sync_docker {

    if [[ $(systemctl is-active docker) != 'active' ]]; then
        echo "starting docker"
        sudo systemctl start docker
    fi

    sudo docker build -t bbilly1/tubearchivist:latest .
    sudo docker push bbilly1/tubearchivist:latest

}

# check package versions in requirements.txt for updates
python version_check.py


if [[ $1 == "blackhole" ]]; then
    sync_blackhole
elif [[ $1 == "test" ]]; then
    sync_test
elif [[ $1 == "docker" ]]; then
    sync_docker
else
    echo "valid options are: blackhole | test | docker"
fi


##
exit 0
