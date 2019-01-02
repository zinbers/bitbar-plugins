#!/usr/bin/env PYTHONIOENCODING=UTF-8 /usr/local/bin/python3
# -*- coding: utf-8 -*-

# <bitbar.title>Gitlab CI</bitbar.title>
# <bitbar.desc>Shows currently running pipelines from your GitLab in your bar. Interested in more advanced GitLab bar integration? Let me know (martin@kluska.cz). This implementation is just quick solution.</bitbar.desc>
# <bitbar.version>v0.21</bitbar.version>
# <bitbar.author>Martin Kluska</bitbar.author>
# <bitbar.author.github>pionl</bitbar.author.github>
# <bitbar.dependencies>python</bitbar.dependencies>
# <bitbar.image>https://raw.githubusercontent.com/pionl/bitbar-gitlab-ci/master/gitlab_ci.png</bitbar.image>
# <bitbar.abouturl>https://github.com/pionl/bitbar-gitlab-ci</bitbar.abouturl>
#

import json

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

# Your private key for accessing gitlab: User -> Settings -> Access tokens -> add personal access token with api scope
PRIVATE_TOKEN = '2tAnn2nH7YkAAfRRyo7L'
# Gitlab URL
URL = 'http://gitlab.mybogame.com'
# Define your server and projects (name: id)
# To get id go to project -> Settings -> General -> General project settings
PROJECTS ={"ab-blast": 1}

pipelines = []

# Converts the gitlab status to emoji
def stateIcon(status):
    return {
        "created": "💤",
        "pending": "💤",
        "running": "🚀",
        "failed": "❗",
        "success": "✔️",
        "skipped": "🚀",
        "manual": "💤"
    }[status]

# Calls gitlab API endpoint with private_token
def api (method):
    url = URL + "/api/v4/" + method
    param = 'private_token=' + PRIVATE_TOKEN
    # Detect if method has query string (we need to append private token)
    url = url + (('&') if "?" in url else ('?')) + param
    body = urlopen(url).read()
    return json.loads(body.decode('utf-8'))

# Project details
class Project:
    def __init__ (self, name, id):
        self.name = name
        self.id = id

# Pipile job
class Job:
    def __init__ (self, json):
        self.name = json["stage"] + (": " + json["name"] if json["name"] != json["stage"] else "" )
        self.status = json["status"]
        self.duration = 0
        if "duration" in json and self.status != "running":
            self.duration=int(json["duration"])
        self.commit = json['commit']['title']

    # Jobs name with duration
    def displayName(self):
        return self.name + (' ' + str(self.duration) + 's' if self.duration > 0 else '')
    
# Pipile
class Pipeline:
    def __init__ (self, projectName, projectId, json):
        self.project = Project(projectName, projectId)
        self.id = json["id"]
        self.jobs = []
        self.runningJobs = []
        self.ref = str(json["ref"])
        self.commit = None

    # Display name with current running jobs
    def displayName(self):
        jobsString = '💤'

        # Get running jobs and append the name
        if len(self.runningJobs) > 0:
            strings = []
            for job in self.runningJobs:
                strings.append(job.displayName()) 

            jobsString = ', '.join(strings)

        return self.project.name + ' - ' + self.ref + ' (' + jobsString + ')'

    # Add jobs array json
    def addJobs(self, jobsArray):
        for jobJson in jobsArray:
            # Parse the job
            job = Job(jobJson)
            # Add the jobs array
            self.jobs.append(job)

            # Get the commit from the first job
            if self.commit is None:
                self.commit = job.commit

            # Check if the job is running for running jobs array
            if job.status == 'running':
                self.runningJobs.append(job)


# Loop the projects and get thy jobs
for name, project in PROJECTS.items():
    runningPipelines = api("projects/"+str(project)+"/pipelines?scope=running")

    for pipelineJson in runningPipelines:
        pipeline = Pipeline(name, project, pipelineJson)
        jobsArray = api("projects/"+str(project)+"/pipelines/"+str(pipeline.id)+"/jobs")
        if len(jobsArray) > 0:
            pipeline.addJobs(jobsArray)
            pipelines.append(pipeline)

pipelineCount = len(pipelines)
if pipelineCount == 0:
    print("💤")
    exit


## Render the pipelines names (bitbar will loop)
for index, pipeline in enumerate(pipelines):
    print('🚀 '),

    if pipelineCount > 1:
        print(str(index + 1) + '/' + str(pipelineCount) + ' '),

    print(pipeline.displayName())


## Start menu
print("---")

for pipeline in pipelines:
    print('🚀 ' + pipeline.project.name + ' - ' + pipeline.ref + '| color=black')
    print('-- commit: ' + pipeline.commit + '| color=black')
    print('---')
    for job in pipeline.jobs:
        print(stateIcon(job.status) + " "),

        style = ''
        if job.status == 'success':
            style = '| color=green'
        elif job.status == 'running':
            style = '| color=blue'

        print(job.displayName() + style)

        