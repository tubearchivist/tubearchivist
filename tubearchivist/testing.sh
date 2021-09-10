#!/bin/bash
# install debug and testing tools into slim container

apt update && apt install -y vim htop bmon net-tools iputils-ping procps

pip install ipython

##
exit 0
