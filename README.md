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

# Apache OpenWhisk runtimes for Python
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![Build Status](https://travis-ci.com/apache/openwhisk-runtime-python.svg?branch=master)](https://travis-ci.com/apache/openwhisk-runtime-python)

## Build Runtimes

### You have 2 options to build the Python runtime:
- Building locally
- Using OpenWhisk Actions.
### This README walks you through how to do both

# Building Python Runtime Locally

### Pre-requisites
- [Docker](https://www.docker.com/)
- [curl](https://curl.se/), [wget](https://www.gnu.org/software/wget/), or [Postman](https://www.postman.com/)

0. Choose/create a folder of your liking
1. Clone this repo:
```
git clone https://github.com/apache/openwhisk-runtime-python
cd openwhisk-runtime-python
```

2. Build docker

Build using Python 3.7 (recommended)
```
docker build -t actionloop-python-v3.7:1.0-SNAPSHOT $(pwd)/core/python3ActionLoop
```

For runtime 3.9 or 3.6-ai you need also to copy `bin` and `lib` folders from 3.7 in the Docker folder.


2.1. Check docker `IMAGE ID` (3rd column) for repository `actionloop-python-v3.7`
```
docker images
```
You should see an image that looks something like:
```
actionloop-python-v3.7         1.0-SNAPSHOT ...
```

2.2. Tag image (Optional step). Required if you’re pushing your docker image to a registry e.g. dockerHub
```
docker tag <docker_image_ID> <dockerHub_username>/actionloop-python-v3.7:1.0-SNAPSHOT
```

3. Run docker on localhost with either the following commands:
```
docker run -p 127.0.0.1:80:8080/tcp --name=bloom_whisker --rm -it actionloop-python-v3.7:1.0-SNAPSHOT
```
Or run the container in the background (Add -d (detached) to the command above)
```
docker run -d -p 127.0.0.1:80:8080/tcp --name=bloom_whisker --rm -it actionloop-python-v3.7:1.0-SNAPSHOT
```
Note: If you run your docker container in the background you'll want to stop it with:
```
docker stop <container_id>
```
Where `<container_id>` is obtained from `docker ps` command bellow

Lists all running containers
```
docker ps
```
or
```
docker ps -a
```
You shoulkd see a container named `bloom_whisker` being run

4. Create your function (note that each container can only hold one function)
In this first example we'll be creating a very simple function
Create a json file called `python-data-init-run.json` which will contain the function that looks something like the following:
NOTE: value of code is the actual payload and must match the syntax of the target runtime language, in this case `python`
```json
{
   "value": {
      "name" : "python-helloworld",
      "main" : "main",
      "binary" : false,
      "code" : "def main(args): return {'payload': 'Hello World!'}"
   }
}
```

To issue the action against the running runtime, we must first make a request against the `init` API
We need to issue `POST` requests to init our function
Using curl (the option `-d` signifies we're issuing a POST request)
```
curl -d "@python-data-init-run.json" -H "Content-Type: application/json" http://localhost/init
```
Using wget (the option `--post-file` signifies we're issuing a POST request)
```
wget --post-file=python-data-init-run.json --header="Content-Type: application/json" http://localhost/init
```
The above can also be achieved with [Postman](https://www.postman.com/) by setting the headers and body accordingly

Client expected response:
```
{"ok":true}
```
Server will remain silent in this case

Now we can invoke/run our function against the `run` API with:
Using curl `POST` request
```
curl -d "@python-data-init-run.json" -H "Content-Type: application/json" http://localhost/run
```
Or using `GET` request
```
curl --data-binary "@python-data-init-run.json" -H "Content-Type: application/json" http://localhost/run
```
Or
Using wget `POST` request. The `-O-` is to redirect `wget` response to `stdout`.
```
wget -O- --post-file=python-data-init-run.json --header="Content-Type: application/json" http://localhost/run
```
Or using `GET` request
```
wget -O- --body-file=python-data-init-run.json --method=GET --header="Content-Type: application/json" http://localhost/run
```

The above can also be achieved with [Postman](https://www.postman.com/) by setting the headers and body accordingly.

You noticed that we’re passing the same file `python-data-init-run.json` from function initialization request to trigger the function. That’s not necessary and not recommended since to trigger a function all we need is to pass the parameters of the function. So in the above example, it's preferred if we create a file called `python-data-params.json` that looks like the following:
```json
{
   "value": {}
}
```
And trigger the function with the following (it also works with wget and postman equivalents):
```
curl --data-binary "@python-data-params.json" -H "Content-Type: application/json" http://localhost/run
```

#### You can perform the same steps as above using [Postman](https://www.postman.com/) application. Make sure you have the correct request type set and the respective body. Also set the correct headers key value pairs, which for us is "Content-Type: application/json"

After you trigger the function with one of the above commands you should expect the following client response:
```
{"payload": "Hello World!"}
```
And Server expected response:
```
XXX_THE_END_OF_A_WHISK_ACTIVATION_XXX
XXX_THE_END_OF_A_WHISK_ACTIVATION_XXX
```

## Creating functions with arguments
If your container still running from the previous example you must stop it and re-run it before proceeding. Remember that each python runtime can only hold one function (which cannot be overrided due to security reasons)
Create a json file called `python-data-init-params.json` which will contain the function to be initialized that looks like the following:
```json
{
   "value": {
      "name": "python-helloworld-with-params",
      "main" : "main",
      "binary" : false,
      "code" : "def main(args): return {'payload': 'Hello ' + args.get('name') + ' from ' + args.get('place') + '!!!'}"
   }
}
```
Also create a json file `python-data-run-params.json` which will contain the parameters to the function used to trigger it. Notice here we're creating 2 separate file from the beginning since this is good practice to make the distinction between what needs to be sent via the `init` API and what needs to be sent via the `run` API:
```json
{
   "value": {
      "name": "UFO",
      "place": "Mars"
   }
}
```

Now, all we have to do is initialize and trigger our function.
First, to initialize our function make sure your python runtime container is running if not, spin the container by following step 3.
Issue a `POST` request against the `init` API with the following command:
Using curl:
```
curl -d "@python-data-init-params.json" -H "Content-Type: application/json" http://localhost/init
```
Using wget:
```
wget --post-file=python-data-init-params.json --header="Content-Type: application/json" http://localhost/init
```
Client expected response:
```
{"ok":true}
```
Server will remain silent in this case

Second, to run/trigger the function issue requests against the `run` API with the following command:
Using curl with `POST`:
```
curl -d "@python-data-run-params.json" -H "Content-Type: application/json" http://localhost/run
```
Or using curl with  `GET`:
```
curl --data-binary "@python-data-run-params.json" -H "Content-Type: application/json" http://localhost/run
```
Or
Using wget with `POST`:
```
wget -O- --post-file=python-data-run-params.json --header="Content-Type: application/json" http://localhost/run
```
Or using  wget with `GET`:
```
wget -O- --body-file=python-data-run-params.json --method=GET --header="Content-Type: application/json" http://localhost/run
```

After you trigger the function with one of the above commands you should expect the following client response:
```
{"payload": "Hello UFO from Mars!!!"}
```

And Server expected response:
```
XXX_THE_END_OF_A_WHISK_ACTIVATION_XXX
XXX_THE_END_OF_A_WHISK_ACTIVATION_XXX
```

## Now let's create a more interesting function
### This function will calculate the nth Fibonacci number
This is the function we’re trying to create. It calculates the nth number of the Fibonacci sequence recursively in `O(n)` time
```python
def fibonacci(n, mem):
   if (n == 0 or n == 1):
      return 1
   if (mem[n] == -1):
      mem[n] = fibonacci(n-1, mem) + fibonacci(n-2, mem)
   return mem[n]

def main(args):
   n = int(args.get('fib_n'))
   mem = [-1 for i in range(n+1)]
   result = fibonacci(n, mem)
   key = 'Fibonacci of n == ' + str(n)
   return {key: result}
```

Create a json file called `python-fib-init.json` to initialize our fibonacci function and insert the following. (It’s the same code as above but since we can’t have a string span multiple lines in JSON we need to put all this code in one line and this is how we do it. It’s ugly but not much we can do here)
```json
{
   "value": {
      "name": "python-recursive-fibonacci",
      "main" : "main",
      "binary" : false,
      "code" : "def fibonacci(n, mem):\n\tif (n == 0 or n == 1):\n\t\treturn 1\n\tif (mem[n] == -1):\n\t\tmem[n] = fibonacci(n-1, mem) + fibonacci(n-2, mem)\n\treturn mem[n]\n\ndef main(args):\n\tn = int(args.get('fib_n'))\n\tmem = [-1 for i in range(n+1)]\n\tresult = fibonacci(n, mem)\n\tkey = 'Fibonacci of n == ' + str(n)\n\treturn {key: result}"
   }
}
```
Create a json file called `python-fib-run.json` which will be used to run/trigger our function with the appropriate argument:
```json
{
   "value": {
      "fib_n": "40"
   }
}
```

Now we’re all set.
Make sure your python runtime container is running if not, spin the container by following step 3.
Initialize our fibonacci function by issuing a `POST` request against the `init` API with the following command:
Using curl:
```
curl -d "@python-fib-init.json" -H "Content-Type: application/json" http://localhost/init
```
Using wget:
```
wget --post-file=python-fib-init.json --header="Content-Type: application/json" http://localhost/init
```
Client expected response:
```
{"ok":true}
```
You've noticed by now that `init` API always returns `{"ok":true}` for a successful initialized function. And the server, again, will remain silent

Trigger the function by running/triggering the function with a request against the `run` API with the following command:
Using curl with `POST`:
```
curl -d "@python-fib-run.json" -H "Content-Type: application/json" http://localhost/run
```
Using curl with `GET`:
```
curl --data-binary "@python-fib-run.json" -H "Content-Type: application/json" http://localhost/run
```
Using wget with `POST`:
```
wget -O- --post-file=python-fib-run.json --header="Content-Type: application/json" http://localhost/run
```
Using wget with `GET`:
```
wget -O- --body-file=python-fib-run.json --method=GET --header="Content-Type: application/json" http://localhost/run
```

After you trigger the function with one of the above commands you should expect the following client response:
```
{"Fibonacci of n == 40": 165580141}
```

And Server expected response:
```
XXX_THE_END_OF_A_WHISK_ACTIVATION_XXX
XXX_THE_END_OF_A_WHISK_ACTIVATION_XXX
```

#### At this point you can edit python-fib-run.json and try other `fib_n` values. All you have to do is save `python-fib-run.json` and trigger the function again. Notice that here we're just modifying the parameters of our function; therefore, there's no need to re-run/re-initialize our container that contains our Python runtime.

#### You can also automate most of this process through [docker actions](https://github.com/apache/openwhisk/tree/master/tools/actionProxy) by using `invoke.py`

# Building Python Runtime using OpenWhisk Actions

### Pre-requisites
- [Gradle](https://gradle.org/)
- [Docker](https://www.docker.com/)
- [OpenWhisk CLI wsk](https://github.com/apache/openwhisk-cli/releases)


The runtimes are built using Gradle.
The file [settings.gradle](settings.gradle) lists the images that are build by default.
To build all those images, run the following command.

```
./gradlew distDocker
```

You can optionally build a specific image by modifying the Gradle command. For example:
```
./gradlew core:python3Action:distDocker
```

The build will produce Docker images such as `action-python-v3.7`
and will also tag the same image with the `whisk/` prefix. The latter
is a convenience, which if you're testing with a local OpenWhisk
stack, allows you to skip pushing the image to Docker Hub.

The image will need to be pushed to Docker Hub if you want to test it
with a hosted OpenWhisk installation.

### Using Gradle to push to a Docker Registry

The Gradle build parameters `dockerImagePrefix` and `dockerRegistry`
can be configured for your Docker Registry. Make sure you are logged
in first with the `docker` CLI.

- Use the `docker` CLI to login. The following assume you will substitute `$DOCKER_USER` with an appropriate value.
  ```
  docker login --username $DOCKER_USER
  ```

- Now build, tag and push the image accordingly.
  ```
  ./gradlew distDocker -PdockerImagePrefix=$DOCKER_USER -PdockerRegistry=docker.io
  ```

### Using Your Image as an OpenWhisk Action

You can now use this image as an OpenWhisk action. For example, to use
the image `action-python-v3.7` as an action runtime, you would run
the following command.

```
wsk action update myAction myAction.py --docker $DOCKER_USER/action-python-v3.7
```

## Test Runtimes

There are suites of tests that are generic for all runtimes, and some that are specific to a runtime version.
To run all tests, there are two steps.

First, you need to create an OpenWhisk snapshot release. Do this from your OpenWhisk home directory.
```
./gradlew install
```

Now you can build and run the tests in this repository.
```
./gradlew tests:test
```

Gradle allows you to selectively run tests. For example, the following
command runs tests which match the given pattern and excludes all
others.
```
./gradlew :tests:test --tests Python*Tests
```

## Python 3 AI Runtime
This action runtime enables developers to create AI Services with OpenWhisk. It comes with preinstalled libraries useful for running machine learning and deep learning inferences. [Read more about this runtime here](./core/python3AiAction).

## Import Project into IntelliJ

Follow these steps to import the project into your IntelliJ IDE.
- Import project as gradle project.
- Make sure the working directory is root of the project/repo.

# Using extra libraries

If you need more libraries for your Python action,  you can include a virtualenv in the zip file of the action.

The requirement is that the zip file must have a subfolder named `virtualenv` with a script `virtualenv\bin\activate_this.py` working in an Linux AMD64 environment. It will be executed at start time to use your extra libraries.

## Using requirements.txt

Virtual envs are usually built listing your dependencies in a `requirements.txt`.

If you have an action that requires addition libraries, you can just include `requirements.txt`.

You have to create a folder `myaction` with at least two files:

```
__main__.py
requirements.txt
```

Then zip your action and deploy to OpenWhisk, the requirements will be installed for you at init time, creating a suitable virtualenv.

Keep in mind that resolving requirements involves downloading and install software, so your action timeout limit may need to be adjusted accordingly. Instead, you should consider using precompilation to resolve the requirements at build time.


## Precompilation of a virtualenv

The action containers can actually generate a virtualenv for you, provided you have a requirements.txt.


If you have an action in the format described before (with a `requirements.txt`) you can build the zip file with the included files with:

```
zip -j -r myaction | docker run -i action-python-v3.7 -compile main >myaction.zip
```

You may use `v3.9` or `v3.6-ai` as well according to your Python version needs.

The resulting action includes a virtualenv already built for you and that is fast to deploy and start as all the dependencies are already resolved. Note that there is a limit on the size of the zip file and this approach will not work for installing large libraries like Pandas or Numpy, instead use the provide "v.3.6-ai"  runtime instead which provides these libraries already for you.
