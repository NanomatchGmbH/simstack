import sys
import time
from pyura import UnicoreAPI, HTTPBasicAuthProvider, ErrorCodes, JobStatus

# insert name
username = "[username]"
# insert password
password = "[password]"
# insert URL pointing to an Unicore REST service
base_uri = "https://unicoreserver.com:8080/SITE/rest/core"

if __name__ == "__main__":
    # first, we initialize the Unicore REST API
    UnicoreAPI.init()

    # second, we need an authentication provider that is used to log in
    auth_provider = HTTPBasicAuthProvider(username, password)

    # then, we request a registry...
    registry = UnicoreAPI.add_registry(base_uri, auth_provider)

    # ... and connect to the Unicore server
    error, status = registry.connect()
    if error == ErrorCodes.NO_ERROR and status == 200:
        print("Connected to %s." % base_uri)
    else:
        print("Connection error, status: %d" % status)
        sys.exit(1)

    # let's list the jobs on the server, so we need a JobManager
    job_manager = registry.get_job_manager()
    job_manager.update_list()

    jobs = job_manager.get_list()
    print("             JOB ID                 \t "\
            "Status \t\t Termination Time")
    for job in jobs:
        print("%s\t%-20s\t%s" % (
            job.get_id(),
            job.get_status(),
            job.get_termination_time())
        )

    # create a simple job, ...
    error, newjob = job_manager.create(
            '/bin/echo',                # command to execute
            arguments=['hallo, welt']   # arguments to above command
        )

    if (error != ErrorCodes.NO_ERROR):
        logger.error("Could _NOT_ add job.")
        sys.exit(1)
    
    # ... start it and ...
    job_manager.start(newjob)

    # ... wait for it to finish.
    jobstatus = newjob.get_status()
    while (
            not (jobstatus == JobStatus.SUCCESSFUL \
                or jobstatus == JobStatus.FAILED
            )
    ):
        print("Waiting for job to finish (status: %s)..." % jobstatus)
        time.sleep(2)
        newjob.update()
        jobstatus = newjob.get_status()
    print("Job finished with status \"%s\"." % jobstatus)
