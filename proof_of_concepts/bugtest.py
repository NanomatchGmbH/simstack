#!/usr/bin/env python2
from __future__ import print_function

import requests
import json
import time

base = "https://yourbase.com:8080/DEMO-SITE/rest/core" 
credentials = ("myuser", "mypass")
print("THIS WILL DELETE ALL YOUR JOBS, REMOVE THE EXIT AFTER YOU READ THIS MESSAGE, if you are ok with this.")
exit(0)

# check that we can access the server
headers = {'Accept': 'application/json'}
r = requests.get(base, auth=credentials, headers=headers, verify=False)

if r.status_code != 200:
    print("Error accessing the server!")
else:
    print("Ready.")
print(json.dumps(r.json(), indent=4))

################# 1. List jobs before (should be ok):
headers = {'Accept': 'application/json'}
r = requests.get(base + "/jobs", headers=headers, auth=credentials, verify=False)
jobList = r.json()
print(json.dumps(jobList, indent=4))
time.sleep(5)

################# 2. Queue a job with staging, don't start it.
job = {'Executable': "/bin/ls", 'Arguments': ["-lisa", "$HOME"], 'haveClientStageIn' : 'true'}
headers = {'content-type': 'application/json'}
r = requests.post(base + "/jobs", data=json.dumps(job), headers=headers, auth=credentials, verify=False)
print(r.status_code)
if r.status_code != 201:
    print("Error submitting job:", end=' ')
else:
    jobURL = r.headers['Location']
    print("Submitted new job at", jobURL)
time.sleep(5)

################  3. List jobs after submit (should be ok):
headers = {'Accept': 'application/json'}
r = requests.get(base + "/jobs", headers=headers, auth=credentials, verify=False)
jobList = r.json()
print(json.dumps(jobList, indent=4))
time.sleep(5)

################ 4. Delete all jobs (gives result 204 for everything - which usually means: all deleted)
headers = {}
for job in jobList["jobs"]:
    r = requests.delete(job,auth=credentials,headers=headers,verify=False)
    print(r.status_code)
time.sleep(5)

################  5. List jobs after submit (Not ok, still contains undeleted jobs):
headers = {'Accept': 'application/json'}
r = requests.get(base + "/jobs", headers=headers, auth=credentials, verify=False)
jobList = r.json()
print(json.dumps(jobList, indent=4))
time.sleep(5)

################ 6. Delete all jobs again (this gives a nullpointer exception in the U/X log)
for job in jobList["jobs"]:
    r = requests.delete(job,auth=credentials,headers=headers,verify=False)
    print(r.status_code)
time.sleep(5)
