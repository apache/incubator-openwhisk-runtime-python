#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# build go proxy from source
FROM golang:1.15 AS builder_source
ARG GO_PROXY_GITHUB_USER=apache
ARG GO_PROXY_GITHUB_BRANCH=master
RUN git clone --branch ${GO_PROXY_GITHUB_BRANCH} \
   https://github.com/${GO_PROXY_GITHUB_USER}/openwhisk-runtime-go /src ;\
   cd /src ; env GO111MODULE=on CGO_ENABLED=0 go build main/proxy.go && \
   mv proxy /bin/proxy

# or build it from a release
FROM golang:1.15 AS builder_release
ARG GO_PROXY_RELEASE_VERSION=1.15@1.17.0
RUN curl -sL \
  https://github.com/apache/openwhisk-runtime-go/archive/${GO_PROXY_RELEASE_VERSION}.tar.gz\
  | tar xzf -\
  && cd openwhisk-runtime-go-*/main\
  && GO111MODULE=on go build -o /bin/proxy

# Dockerfile for python AI actions, overrides and extends ActionRunner from actionProxy
FROM tensorflow/tensorflow:1.15.2-py3-jupyter

# select the builder to use
ARG GO_PROXY_BUILD_FROM=source

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
            curl \
            gcc \
            libc-dev \
            libxslt-dev \
            libxml2-dev \
            libffi-dev \
            libssl-dev \
            zip \
            unzip \
            vim \
            && rm -rf /var/lib/apt/lists/*

# PyTorch
# persistent as it fails often
RUN while ! pip list | grep torch ;\
    do pip install torch ; done ;\
    while ! pip list | grep torchvision ;\
    do pip install torchvision ; done

# rclone
RUN curl -L https://downloads.rclone.org/rclone-current-linux-amd64.deb -o rclone.deb \
    && dpkg -i rclone.deb \
    && rm rclone.deb

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip six wheel &&\
    pip3 install --no-cache-dir -r requirements.txt &&\
    ln -sf /usr/bin/python3 /usr/local/bin/python

RUN mkdir -p /action
WORKDIR /

COPY --from=builder_source /bin/proxy /bin/proxy_source
COPY --from=builder_release /bin/proxy /bin/proxy_release
RUN mv /bin/proxy_${GO_PROXY_BUILD_FROM} /bin/proxy

ADD bin/compile /bin/compile
ADD lib/launcher.py /lib/launcher.py

# log initialization errors
ENV OW_LOG_INIT_ERROR=1
# the launcher must wait for an ack
ENV OW_WAIT_FOR_ACK=1
# using the runtime name to identify the execution environment
ENV OW_EXECUTION_ENV=openwhisk/action-python-v3.6-ai
# compiler script
ENV OW_COMPILER=/bin/compile
# use utf-8
ENV PYTHONIOENCODING=UTF-8
ENTRYPOINT ["/bin/proxy"]
