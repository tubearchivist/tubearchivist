#!/bin/bash

# deploy all needed project files to different servers:
# test for local vm for testing
# blackhole for local production
# docker to publish

# create builder:
# docker buildx create --name tubearchivist
# docker buildx use tubearchivist
# docker buildx inspect --bootstrap

# more details:
# https://github.com/bbilly1/tubearchivist/issues/6

set -e

function sync_blackhole {

    # docker commands need sudo, only build amd64
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

    echo "$PASS" | ssh "$host" 'sudo -S docker buildx build --platform linux/amd64 -t bbilly1/tubearchivist:latest tubearchivist --load 2>/dev/null'
    echo "$PASS" | ssh "$host" 'sudo -S docker-compose up -d 2>/dev/null'

}

function sync_test {

    # docker commands don't need sudo in testing vm
    # pass argument to build for specific platform

    host="tubearchivist.local"

    rsync -a --progress --delete-after \
        --exclude ".git" \
        --exclude ".gitignore" \
        --exclude "**/cache" \
        --exclude "**/__pycache__/" \
        --exclude "db.sqlite3" \
        . -e ssh "$host":tubearchivist

    rsync -r --progress --delete docker-compose.yml -e ssh "$host":docker

    if [[ $1 = "amd64" ]]; then
        platform="linux/amd64"
    elif [[ $1 = "arm64" ]]; then
        platform="linux/arm64"
    elif [[ $1 = "multi" ]]; then
        platform="linux/amd64,linux/arm64"
    else
        platform="linux/amd64"
    fi

    ssh "$host" "docker buildx build --platform $platform -t bbilly1/tubearchivist:latest tubearchivist --load"
    ssh "$host" 'docker-compose -f docker/docker-compose.yml up -d'

    ssh "$host" 'docker cp tubearchivist/tubearchivist/testing.sh tubearchivist:/app/testing.sh'
    ssh "$host" 'docker exec tubearchivist chmod +x /app/testing.sh'

}


# run same tests and checks as with github action but locally
# takes filename to validate as optional argument
function validate {

    if [[ $1 ]]; then
        check_path="$1"
    else
        check_path="."
    fi

    echo "run validate on $check_path"
    
    echo "running bandit"
    bandit --recursive --skip B105,B108,B404,B603,B607 "$check_path"
    echo "running black"
    black --diff --color --check -l 79 "$check_path"
    echo "running codespell"
    codespell --skip="./.git" "$check_path"
    echo "running flake8"
    flake8 "$check_path" --count --max-complexity=12 --max-line-length=79 \
        --show-source --statistics
    echo "running isort"
    isort --check-only --diff --profile black -l 79 "$check_path"
    printf "    \n> all validations passed\n"

}


function sync_docker {

    # check things
    if [[ $(git branch --show-current) != 'master' ]]; then
        echo 'you are not on master, dummy!'
        return
    fi

    if [[ $(systemctl is-active docker) != 'active' ]]; then
        echo "starting docker"
        sudo systemctl start docker
    fi

    echo "latest tags:"
    git tag

    echo "latest docker images:"
    sudo docker image ls bbilly1/tubearchivist

    printf "\ncreate new version:\n"
    read -r VERSION

    echo "build and push $VERSION?"
    read -rn 1

    # start build
    sudo docker buildx build \
        --platform linux/amd64,linux/arm64 \
        -t bbilly1/tubearchivist:latest \
        -t bbilly1/tubearchivist:"$VERSION" --push .

    # create release tag
    echo "commits since last version:"
    git log "$(git describe --tags --abbrev=0)"..HEAD --oneline
    git tag -a "$VERSION" -m "new release version $VERSION"
    git push all "$VERSION"

}


# check package versions in requirements.txt for updates
python version_check.py


if [[ $1 == "blackhole" ]]; then
    sync_blackhole
elif [[ $1 == "test" ]]; then
    sync_test "$2"
elif [[ $1 == "validate" ]]; then
    validate "$2"
elif [[ $1 == "docker" ]]; then
    sync_docker
else
    echo "valid options are: blackhole | test | validate | docker"
fi


##
exit 0
