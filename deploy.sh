#!/bin/bash

# deploy all needed project files to different servers:
# test for local vm for testing
# blackhole for local production
# unstable to publish intermediate releases
# docker to publish regular release

# create builder:
# docker buildx create --name tubearchivist
# docker buildx use tubearchivist
# docker buildx inspect --bootstrap

# more details:
# https://github.com/tubearchivist/tubearchivist/issues/6

set -e

function sync_blackhole {

    host="blackhole.local"
    
    rsync -a --progress --delete-after \
        --exclude ".git" \
        --exclude ".gitignore" \
        --exclude "**/cache" \
        --exclude "**/__pycache__/" \
        --exclude ".venv" \
        --exclude "db.sqlite3" \
        --exclude ".mypy_cache" \
        . -e ssh "$host":tubearchivist

    ssh "$host" 'docker build -t bbilly1/tubearchivist --build-arg TARGETPLATFORM="linux/amd64" tubearchivist'
    ssh "$host" 'docker compose up -d'

}

function sync_test {

    # docker commands don't need sudo in testing vm
    # pass argument to build for specific platform

    host="tubearchivist.local"
    # make base folder
    ssh "$host" "mkdir -p docker"

    # copy project files to build image
    rsync -a --progress --delete-after \
        --exclude ".git" \
        --exclude ".gitignore" \
        --exclude "**/cache" \
        --exclude "**/__pycache__/" \
        --exclude "**/.pytest_cache/" \
        --exclude ".venv" \
        --exclude "db.sqlite3" \
        --exclude ".mypy_cache" \
        . -e ssh "$host":tubearchivist

    # copy default docker-compose file if not exist
    rsync --progress --ignore-existing docker-compose.yml -e ssh "$host":docker

    if [[ $1 = "amd64" ]]; then
        platform="linux/amd64"
    elif [[ $1 = "arm64" ]]; then
        platform="linux/arm64"
    elif [[ $1 = "multi" ]]; then
        platform="linux/amd64,linux/arm64"
    else
        platform="linux/amd64"
    fi

    ssh "$host" "docker buildx build --build-arg INSTALL_DEBUG=1 --platform $platform -t bbilly1/tubearchivist:latest tubearchivist --load"
    ssh "$host" 'docker compose -f docker/docker-compose.yml up -d'

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

    # note: this logic is duplicated in the `./github/workflows/lint_python.yml` config
    # if you update this file, you should update that as well
    echo "running black"
    black --force-exclude "migrations/*" --diff --color --check -l 79 "$check_path"
    echo "running codespell"
    codespell --skip="./.git,./.venv,./package.json,./package-lock.json,./node_modules,./.mypy_cache" "$check_path"
    echo "running flake8"
    flake8 "$check_path" --exclude "migrations,.venv" --count --max-complexity=10 \
        --max-line-length=79 --show-source --statistics
    echo "running isort"
    isort --skip "migrations" --skip ".venv" --check-only --diff --profile black -l 79 "$check_path"
    printf "    \n> all validations passed\n"

}


# update latest tag compatible es for set and forget
function sync_latest_es {

    VERSION=$(grep "bbilly1/tubearchivist-es" docker-compose.yml | awk '{print $NF}')
    printf "\nsync new ES version %s\nContinue?\n" "$VERSION"
    read -rn 1

    if [[ $(systemctl is-active docker) != 'active' ]]; then
        echo "starting docker"
        sudo systemctl start docker
    fi

    sudo docker image pull docker.elastic.co/elasticsearch/elasticsearch:"$VERSION"

    sudo docker tag \
        docker.elastic.co/elasticsearch/elasticsearch:"$VERSION" \
        bbilly1/tubearchivist-es

    sudo docker tag \
        docker.elastic.co/elasticsearch/elasticsearch:"$VERSION" \
        bbilly1/tubearchivist-es:"$VERSION"

    sudo docker push bbilly1/tubearchivist-es
    sudo docker push bbilly1/tubearchivist-es:"$VERSION"

}


# publish unstable tag to docker
function sync_unstable {

    if [[ $(systemctl is-active docker) != 'active' ]]; then
        echo "starting docker"
        sudo systemctl start docker
    fi

    # start amd64 build
    sudo docker buildx build \
        --platform linux/amd64 \
        -t bbilly1/tubearchivist:unstable --push .

}


# new function, sync only tag, build with build server
function sync_docker {

    # check things
    if [[ $(git branch --show-current) != 'master' ]]; then
        echo 'you are not on master, dummy!'
        return
    fi

    echo "latest tags:"
    git tag | sort -rV | head -n 5

    printf "\ncreate new version:\n"
    read -r VERSION

    echo "push new tag: $VERSION?"
    read -rn 1

    # create release tag
    echo "commits since last version:"
    git log "$(git describe --tags --abbrev=0)"..HEAD --oneline
    git tag -a "$VERSION" -m "new release version $VERSION"
    git push origin "$VERSION"

}


# old builder, sync tag, build and push locally
function sync_docker_old {

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
    git tag | sort -rV | head -n 5

    printf "\ncreate new version:\n"
    read -r VERSION

    echo "build and push $VERSION?"
    read -rn 1

    # start build
    sudo docker buildx build \
        --platform linux/amd64,linux/arm64 \
        -t bbilly1/tubearchivist \
        -t bbilly1/tubearchivist:unstable \
        -t bbilly1/tubearchivist:"$VERSION" --push .

    # create release tag
    echo "commits since last version:"
    git log "$(git describe --tags --abbrev=0)"..HEAD --oneline
    git tag -a "$VERSION" -m "new release version $VERSION"
    git push origin "$VERSION"

}


if [[ $1 == "blackhole" ]]; then
    sync_blackhole
elif [[ $1 == "test" ]]; then
    sync_test "$2"
elif [[ $1 == "validate" ]]; then
    validate "$2"
elif [[ $1 == "docker" ]]; then
    sync_docker
elif [[ $1 == "unstable" ]]; then
    sync_unstable
elif [[ $1 == "es" ]]; then
    sync_latest_es
else
    echo "valid options are: blackhole | test | validate | docker | unstable | es"
fi


##
exit 0
