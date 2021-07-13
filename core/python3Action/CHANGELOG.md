<!--
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
-->

# Python 3 OpenWhisk Runtime Container

# to include
 - Use 1.17.1 of openwhisk-runtime-go to support symlinks in zips (required for virtualenvs)
 - Support for python-3.9
 - Support for generating actions with virtualenvs resolving requirements.txt

## 1.16.0
  - Introduce tutorial to deploy python runtimes locally (#101)
  - Use 1.17.0 release of openwhisk-runtime-go (#98)
  - Remove Python2
  - Remove non-actionloop runtimes

## 1.15.0
  - Build proxy from 1.16.0 release of openwhisk-runtime-go
  - Update to golang:1.15 and buster. (#90)
  - Ambiguous name changed to python3ActionLoop (#89)
  - Updated Python runtimes to use "Action Loop" Proxy with new async handshake (#82)

