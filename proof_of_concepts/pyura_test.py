import os
import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import time
import logging
import requests
import random
import filecmp

from pyura import Registry
from pyura import HTTPBasicAuthProvider
from pyura import ErrorCodes, JobStatus

#TODO there should be no import required...
# this is here because of JobManager.Imports
from pyura import JobManager

logger = None

def is_valid_status(status):
    return status >= 200 and status < 300

def connect_callback(calling_object, error_code, status_code):
    logger.info("connect_callback: connection to %s returned %s (%d)" % (
        calling_object, error_code, status_code)
    )

def upload_callback(uploaded_size, total_size):
    percent = uploaded_size * 1e2 / total_size
    sys.stderr.write("\rUploaded: {percent:3.0f}%".format(percent=percent))

def download_callback(downloaded_size, total_size):
    percent = downloaded_size * 1e2 / total_size
    sys.stderr.write("\rDownloaded: {percent:3.0f}% {dl:9.0f}".format(percent=percent, dl=downloaded_size))

if __name__ == "__main__":
    # bad behavior
    requests.packages.urllib3.disable_warnings()
    ############################

    FORMAT = '%(asctime)-15s %(name)-8s %(levelname)-6s %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FORMAT)
    logger = logging.getLogger('pyura')
    logging.info('Started')

    #auth_provider = HTTPBasicAuthProvider('flo_test','flo123test')
    auth_provider = HTTPBasicAuthProvider("timo_test", "asdyxc")

    reg = Registry(
            'https://int-nanomatchcluster.int.kit.edu:8080/NANO-SITE/rest/core',
            auth_provider
            )
    # reg = Registry('https://localhost:12345/NANO-SITE/rest/core', auth_provider)
    logger.info("connect: %s " % str(reg.connect()))
    logger.info("connect (with callback): %s " % str(reg.connect(callback=connect_callback)))
    logger.info("connected as user: %s" % reg.get_user())


    # En-/Disable tests
    test_job_manager        = True
    test_storage_manager    = True
    test_job_imports        = True


    #################################################
    #             TEST: Job Management              #
    #################################################

    if (test_job_manager):
        logger.info("\n"\
                "######################################\n"\
                "              Test: Job Management           \n"\
                "######################################\n"\
                )
        job_manager = reg.get_job_manager()
        if (job_manager is None):
            logger.error("job tests: did NOT get job manager")
        else:
            logger.info("job tests: got job manager")

            job_manager.update_list()
            jobs = job_manager.get_list()
            logger.info("job tests: got %d jobs." % len(jobs))
            ## init all objects. Do not output anything, this will spam the log anyway...
            #for job in jobs:
            #    try:
            #        a = job.get_owner_dn()
            #    except:
            #        # This should not happen when the REST API Bugs are fixed
            #        pass
            logger.info("job tests: job infos:")
            for job in jobs:
                owner = None
                try:
                   owner = job.get_owner_dn()
                except:
                   # This should not happen when the REST API Bugs are fixed
                   pass
                logger.info("   job %s from %s" % (str(job.get_id()), owner))

            err, newjob = job_manager.create('/bin/echo',
                    arguments=['hallo, welt', '$FOO'],
                    environment=["FOO=bar"])

            if (err != ErrorCodes.NO_ERROR):
                logger.error("job tests: could _NOT_ add job.")
                sys.exit(1)
            
            job_manager.start(newjob)

            jobstatus = newjob.get_status()
            logger.info("job tests: created new job (%s), %s" % (
                newjob.get_id(), jobstatus))
            while (not (jobstatus == JobStatus.SUCCESSFUL or jobstatus == JobStatus.FAILED)):
                logger.info("job tests: \twaiting for job to finish (status: %s)...",
                        jobstatus)
                time.sleep(10)
                newjob.update()
                jobstatus = newjob.get_status()
            logger.info("job tests: job finished with status \"%s\".", jobstatus)

            newjob_wd = newjob.get_working_dir()
            storage_manager = reg.get_storage_manager()

            storage_manager.update_list()
            storage = storage_manager.get_by_id(newjob_wd)
            logger.info("job tests: got working directory storage: %s", str(storage))
            storage_manager.select(storage)

            files = storage_manager.get_file_list(storage_id=newjob_wd)
            logger.info("job tests: files in new job's working directory:")
            for  f in files:
                logger.info("\t\t%s", f)

            files = []
            files = storage_manager.get_file_list()
            logger.info("job tests: files in new job's working directory (no args):")
            for  f in files:
                logger.info("\t\t%s", f)


            # Restart
            #TODO maybe we need some kind of long(er) runnnig job to test this.
            job_manager.restart(newjob)
            jobstatus = newjob.get_status()
            logger.info("job tests: restarted job (%s), %s" % (
                newjob.get_id(), jobstatus))

            job_manager.abort(newjob)
            time.sleep(10)
            jobstatus = newjob.get_status()
            i = 10
            while (not (jobstatus == JobStatus.RUNNING) and i > 0):
                jobstatus = newjob.get_status()
                print(jobstatus)
                time.sleep(2)
                i =- 1

            if (jobstatus == JobStatus.ABORTED \
                        or newjob.get_status_msg() == "Job was aborted by the user."):
                logger.info("job tests: aborted job (%s):\n"\
                    "Status: %s\n"\
                    "Message: %s",
                    newjob.get_id(),
                    jobstatus,
                    newjob.get_status_msg()
                    )
            else:
                logger.error("job tests: aborting job (%s) failed, status is %s" % (
                    newjob.get_id(), jobstatus))

            status, err = job_manager.delete(newjob)
            if (is_valid_status(status) and err == ErrorCodes.NO_ERROR):
                logger.info("job tests: deleted job (%s) sucessfully.")
            else:
                logger.error("job tests: could not delete job (%s). status: %d, "\
                        "err: %s" % (newjob.get_id(), status, str(err)))


    #################################################
    #            TEST: File Management              #
    #################################################


    if (test_storage_manager):
        logger.info("\n"\
                "######################################\n"\
                "              Test: File Management           \n"\
                "######################################\n"\
                )
        storage_manager = reg.get_storage_manager()

        if (storage_manager is None):
            logger.error("storage tests: did NOT get manager")
        else:
            logger.info("storage tests: got manager")
            
            # for sake of simplicity, we use this script as testfile
            tfile = os.path.abspath(__file__)
#            tfile = '/tmp/bigfile'
            remote_filename = "test_file_%f.py" % time.time()
            local_file = os.path.join('/tmp', remote_filename)

            storage_manager.update_list()
            logger.info('Storage sites: \n%s',
                    '\n'.join([s.get_id() for s in storage_manager.get_list()]))

            # Upload
            status, err, json = storage_manager.upload_file(tfile,
                    remote_filename=remote_filename,
                    callback=upload_callback)

            if (err != ErrorCodes.NO_ERROR):
                logger.error("storage tests: upload _NOT_ successfull: %s", err)
            else:
                logger.info("storage tests: upload successfull")

                # Download
                status, err = storage_manager.get_file(remote_filename,
                        local_file,
                        callback=download_callback)

                if (err != ErrorCodes.NO_ERROR): 
                    logger.error("storage tests: download _NOT_ successfull: %s %s",
                            err, status)
                else:
                    logger.info("storage tests: download successfull")

                    if (filecmp.cmp(tfile, local_file, shallow=False)):
                        logger.info("storage test: downloaded file matches uploaded file.")
                    else:
                        logger.error("storage test: downloaded file does not match: %s", err)

                    # Delete the downloaded file (remote)
                    status, err = storage_manager.delete_file(remote_filename)
                    if (is_valid_status(status) and err == ErrorCodes.NO_ERROR):
                        logger.info("storage test: remote file deleted.")
                    else:
                        logger.error("storage test: could not delete remote file\n" \
                                "Please delete file %s manually." % remote_filename)

            # Testing download and deletion of non existent files

            remote_filename = "filename_%d.random" % random.randint(100000,9999999)
            local_file = os.path.join('/tmp', remote_filename)

            status, err = storage_manager.get_file(remote_filename, local_file)
            
            if (err == ErrorCodes.NO_ERROR):
                logger.error("storage test: no error returned when downloading non-" \
                        "existent files.")
            #TODO does this return 404???
            elif (status >= 400 and status < 500):
                logger.info("storage test: got correct status code indicating client error: %d.", status)
            else:
                logger.error("storage test: got unexpected status code: %d" % status)

                            
            status, err = storage_manager.delete_file(remote_filename)
            if (is_valid_status(status) or err == ErrorCodes.NO_ERROR):
                logger.error("storage test: no error returned when deleting non-" \
                        "existent files. (%s, %s)", err, status)
            #TODO unicore does not (yet) return any error when deleting a non-existant file
            elif (status >= 400 and status < 500):
                logger.info("storage test: got correct status code indicating client error: %d.", status)
            else:
                logger.error("storage test: got unexpected status code: %d" % status)



    



    #################################################
    #             TEST: Job Imports                 #
    #################################################

    if (test_job_imports):
        logger.info("\n"\
                "######################################\n"\
                "              Test: Job Imports           \n"\
                "######################################\n"\
                )
        job_manager = reg.get_job_manager()
        storage_manager = reg.get_storage_manager()
        fail = False
        output_file = os.path.join('/tmp/job_stdout')
        import_from = os.path.abspath(__file__)
        no_of_imports = 3


        if (job_manager is None
            and storage_manager is None):
            logger.error("job imports: did NOT get job or storage manager")
            fail = True
        else:
            logger.info("job imports: got job manager")

        if not fail:
            imports = JobManager.Imports()

            for i in range(0, no_of_imports):
                imports.add_import(import_from, 'file_%d.py' % i)

            i = len(imports.get_imports())
            if i != no_of_imports:
                logger.error("job imports: not all imports were created... (%d/%d)",
                        i, no_of_imports)
            else:
                logger.info("job imports: all imports created... (%d/%d)",
                        i, no_of_imports)
                
                print("ftu: ", (len(imports.get_imports_to_upload())))

                err, newjob = job_manager.create('/bin/ls',
                        arguments=['-lah', 'file_*.py'],
                        imports=imports,
                        environment=["FOO=bar"])

                if (err == ErrorCodes.NO_ERROR):
                    status, err = job_manager.upload_imports(newjob, storage_manager)
                    if (err == ErrorCodes.NO_ERROR):
                        logger.info("job imports: all files uploaded.")
                    else:
                        logger.error("job imports: not all files uploaded.")
                        fail = True
                else:
                    logger.error("job imports: job creation failed.")

            # All files should be in the job directory, run the job to control!
            if not fail:
                job_manager.start(newjob)
                jobstatus = newjob.get_status()
                while (not (jobstatus == JobStatus.SUCCESSFUL or jobstatus == JobStatus.FAILED)):
                    logger.info("job imports: \twaiting for job to finish (status: %s)...",
                            jobstatus)
                    time.sleep(10)
                    newjob.update()
                    jobstatus = newjob.get_status()
                logger.info("job imports: job finished with status \"%s\".", jobstatus)

                storage_manager.get_file(
                        'stdout',
                        output_file,
                        storage_id=newjob.get_working_dir())

                with open(output_file, 'r') as of:
                    lines = of.readlines()
                    for i in imports.get_imports():
                        found = False
                        f = i['To']
                        for l,line in enumerate(lines):
                            if line.rfind(f) >= 0:
                                found = True
                                print("found %s in %s" % (f, line))
                                lines.pop(l)
                                break
                            
                        if not found:
                            logger.error("job imports: file '%s' is missing in output.",
                                    f)
                            fail = True
                            break
                if not fail:
                    logger.info("job imports: all imports found.")

                status, err = job_manager.delete(newjob)
            
            ########################################
            # New test: what happens if we do not upload the imports?

            fail = False
            imports = JobManager.Imports()

            imports.add_import(import_from, 'file.py')
            imports.add_import("u6://DEMO-SITE/Home/testfile", "otherUspaceFile")

            err, newjob = job_manager.create('/bin/ls',
                    arguments=['-lah'],
                    imports=imports,
                    environment=["FOO=bar"])

            if (err == ErrorCodes.NO_ERROR):
                logger.info("job imports: job created.")
            else:
                logger.error("job imports: job creation failed.")

            if not fail:
                job_manager.start(newjob)
                jobstatus = newjob.get_status()
                while (not (jobstatus == JobStatus.SUCCESSFUL or jobstatus == JobStatus.FAILED)):
                    logger.info("job imports: \twaiting for job to finish (status: %s)...",
                            jobstatus)
                    time.sleep(10)
                    newjob.update()
                    jobstatus = newjob.get_status()
                logger.info("job imports: job finished with status \"%s\".", jobstatus)
                if (jobstatus == JobStatus.FAILED):
                    logger.info("job imports: This job was expected to fail.\nReason (status code: %s):\n%s",
                        newjob.get_exit_code(),
                        newjob.get_status_msg())
                else:
                    logger.error("job imports: Job did not fail as expected.")
                status, err = job_manager.delete(newjob)


            logger.info("job imports: all tests completed successfully.")



                    
    logging.info('Finished')
