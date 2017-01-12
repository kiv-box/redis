#!/bin/bash

REDIS_VERSION='3.2.6'

mkdir -p target/
wget http://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz
tar -xf redis-${REDIS_VERSION}.tar.gz -C target/
cp -r debian target/redis-${REDIS_VERSION}

apt-get install -y \
debhelper \
dh-systemd \
libjemalloc-dev \
procps \
tcl

cd target/redis-${REDIS_VERSION}
dh binary
