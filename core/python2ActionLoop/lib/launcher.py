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
from __future__ import print_function
from os import fdopen
import sys, os, codecs, json, traceback, warnings

sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

try:
  # if the directory 'virtualenv' is extracted out of a zip file
  path_to_virtualenv = os.path.abspath('./virtualenv')
  if os.path.isdir(path_to_virtualenv):
    # activate the virtualenv using activate_this.py contained in the virtualenv
    activate_this_file = path_to_virtualenv + '/bin/activate_this.py'
    if os.path.exists(activate_this_file):
      with open(activate_this_file) as f:
        code = compile(f.read(), activate_this_file, 'exec')
        exec(code, dict(__file__=activate_this_file))
    else:
      sys.stderr.write('Invalid virtualenv. Zip file does not include /virtualenv/bin/' + os.path.basename(activate_this_file) + '\n')
      sys.exit(1)
except Exception:
  traceback.print_exc(file=sys.stderr, limit=0)
  sys.exit(1)

# now import the action as process input/output
from main__ import main as main

env = os.environ
out = fdopen(3, "wb")
if os.getenv("__OW_WAIT_FOR_ACK", "") != "":
  out.write(json.dumps({"ok": True}, ensure_ascii=False).encode('utf-8'))
  out.write(b'\n')
  out.flush()
while True:
  line = sys.stdin.readline().decode('utf-8')
  if not line: break
  args = json.loads(line)
  payload = {}
  for key in args:
    akey = key.encode("ascii", "ignore")
    if akey == "value":
      payload = args["value"]
    else:
      env["__OW_%s" % akey.upper()] = args[key].encode("ascii", "ignore")
  res = {}
  try:
    res = main(payload)
  except Exception as ex:
    print(traceback.format_exc(), file=sys.stderr)
    res = {"error": str(ex)}
  out.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
  out.write(b'\n')
  sys.stdout.flush()
  sys.stderr.flush()
  out.flush()
