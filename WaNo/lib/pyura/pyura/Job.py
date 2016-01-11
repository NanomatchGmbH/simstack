"""
pyura.Job
~~~~~~~~~
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from pyura.ServerPrimitive import ServerPrimitive
from functools import wraps
from pyura.Constants import URIs, JobStatus, ResourceStatus, ErrorCodes
from pyura.helpers import get_enum_by_str, check_safety, convert_date_time
from datetime import datetime
from pyura.Exceptions import *

class Job(ServerPrimitive):
    """This class represents an Unicore Job.
    """

    def _set_status(self, status):
        if (not status is None):
            check_safety([(status, JobStatus)])
            self.status = status

    def _set_resource_status(self, resource_status):
        if (not resource_status is None):
            check_safety([(resource_status, ResourceStatus)])
            self.resource_status = resource_status

    def _set_working_dir(self, working_dir):
        """Sets the id of the Storage that represents the working directory

        Args:
            working_dir (str): the storage id 
        """
        if (not working_dir is None):
            check_safety([(working_dir, str)])
            self.working_dir = working_dir

    def _set_current_time(self, current_time):
        """Sets the time when the properties of this job were updated.

        Args:
            current_time (str): the time of update
        """
        if (not current_time is None):
            check_safety([(current_time, datetime)])
            self.current_time = current_time

    def _set_termination_time(self, termination_time):
        if (not termination_time is None):
            check_safety([(termination_time, datetime)])
            self.termination_time = termination_time

    def _set_submission_time(self, submission_time):
        if (not submission_time is None):
            check_safety([(submission_time, datetime)])
            self.submission_time = submission_time

    def _set_acl(self, acl):
        if (not acl is None):
            check_safety([(acl, str)])
            self.acl = acl

    def _set_queue(self, queue):
        if (not queue is None):
            check_safety([(queue, str)])
            self.queue = queue

    def _set_parent_tss(self, parent_tss):
        """Sets the id of the Site this job is/was run on

        Args:
            parent_tss (str): the site id 
        """
        if (not parent_tss is None):
            check_safety([(parent_tss, str)])
            self.parent_tss = parent_tss

    def _set_owner_dn(self, owner_dn):
        if (not owner_dn is None):
            check_safety([(owner_dn, str)])
            self.owner_dn = owner_dn

    def _set_exit_code(self, exit_code):
        if (not exit_code is None):
            check_safety([(exit_code, str)])
            self.exit_code = exit_code

    def _set_status_msg(self, status_msg):
        if (not status_msg is None):
            check_safety([(status_msg, str)])
            self.status_msg = status_msg

    def update_from_json(self, json):
        # Documented in parent class.
        self._set_status(get_enum_by_str(JobStatus, json['status']))
        self._set_resource_status(
            get_enum_by_str(ResourceStatus, json['resourceStatus'])
        )
        self._set_working_dir(json['workingDirectory'].split('/')[-1])
        #TODO rename request time
        self._set_current_time(convert_date_time(json['currentTime']))
        self._set_termination_time(convert_date_time(json['terminationTime']))
        self._set_submission_time(convert_date_time(json['submissionTime']))
        #TODO self._set_acl()
        self._set_queue(json['queue'])
        self._set_parent_tss(json['parentTSS'].split('/')[-1])
        self._set_owner_dn(json['owner'])
        self._set_status_msg(json['statusMessage'])

        if 'exitCode' in json:
            self._set_exit_code(json['exitCode'])

    def update(self):
        # Documented in parent class.
        self._update(URIs['job_sigle_job'])

    @ServerPrimitive._check_init
    def get_status(self):
        """Returns the :class:`Constants.JobStatus` of this job.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status (:class:`Constants.JobStatus`):  status of this job.
        """
        return self.status

    @ServerPrimitive._check_init
    def get_resource_status(self):
        """Returns the :class:`Constants.ResourceStatus` of this job.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status (:class:`Constants.ResourceStatus`):  status of this job.
        """
        return self.resource_status

    @ServerPrimitive._check_init
    def get_working_dir(self):
        """Returns the id of the Storage that represents the working directory.

        Using the returned id, a storage object can be requested from the
        :class:`StorageManager.StorageManager`.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            working_dir: the storage id
        """
        return self.working_dir

    @ServerPrimitive._check_init
    def get_current_time(self):
        """Returns the time when the properties of this job were updated.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            current_time: the time of update
        """
        return self.current_time

    @ServerPrimitive._check_init
    def get_termination_time(self):
        """Returns the time when this job terminated.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            termination_time: the time when this job terminated.
        """
        return self.termination_time

    @ServerPrimitive._check_init
    def get_acl(self):
        """Returns the ACLs of this job.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

            .. note:: Due to a lack of Unicore documentation, this method is not
                yet fully implemented.
        
        Returns:
            acl: the ACLs of this job
        """
        return self.acl

    @ServerPrimitive._check_init
    def get_queue(self):
        """Returns the queue this job is currently listed in.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            queue: the queue this job is currently listed in.
        """
        return self.queue

    @ServerPrimitive._check_init
    def get_parent_tss(self):
        """Returns the id of the Site this job is/was run on.

        Using the returned id, a site object can be requested from the
        :class:`SiteManager.SiteManager`.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            parent_tss: the site id
        """
        return self.parent_tss

    @ServerPrimitive._check_init
    def get_owner_dn(self):
        """Returns the DN (distinguished name) of the user owning this job.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            dn (str): the DN of the user owning this job.
        """
        return self.owner_dn

    @ServerPrimitive._check_init
    def get_submission_time(self):
        """Returns the submission time of this job.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            submission_time: the time this job has been submitted.
        """
        return self.submission_time

    @ServerPrimitive._check_init
    def get_exit_code(self):
        """Returns the exit code returned after the job execution.
        
            .. note:: The returned exit code is only valid,
                if Job.get_status() returns
                either Constants.JobStatus.FAILED
                or Constants.JobStatus.SUCCESSFUL.
                Otherwise, the job has not been executed (at all) and the exit
                code does not have any meaning.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        
        Returns:
            exit_code: the exit code
        """
        return self.exit_code

    @ServerPrimitive._check_init
    def get_status_msg(self):
        """Returns the status message of this job.
        
        This message for example contains further information on errors.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status_msg (str): the status message.
        """
        return self.status_msg

    def get_imports(self):
        """Returns the :class:`JobManager.Imports` assigned to this job.

        Returns:
            imports (:class:`JobManager.Imports`): the imports assigned
            to this job.
        """
        return self.imports

    def imports_require_upload(self):
        """Checks if any (at least one) of the imports assigned to this job
        requires a file upload before the job execution can be started on the
        server.

        Returns:
            true, if a file upload is required.
        """
        to_upload = self.imports.get_imports_to_upload()
        return ((to_upload != []), to_upload)

    def _reset_init(self):
        """This method is required to reset the state variable that indicates
        if the properties of this Job instance have been fetched from the
        Server recently.
        This should only be reset by the JobManager in cases where a change of
        the job probperties is expected.
        """
        self.init               = False

    def __init__(self, id, connection, imports=[]):
        super(Job, self).__init__(id)
        self.con                = connection #TODO move into superclass
        self.imports            = imports
        self.exit_code          = None
        self.init               = False
        self.status             = None
        self.resource_status    = None
        self.working_dir        = None
        self.current_time       = None
        self.termination_time   = None
        self.acl                = None
        self.queue              = None
        self.parent_tss         = None
        self.owner_dn           = None
        self.submission_time    = None
        self.exit_code          = None
        self.status_msg         = None


