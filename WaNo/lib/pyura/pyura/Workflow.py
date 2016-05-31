"""
pyura.Workflow
~~~~~~~~~
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .ServerPrimitive import ServerPrimitive
from functools import wraps
from .Constants import URIs, JobStatus, ResourceStatus, ErrorCodes
from .helpers import get_enum_by_str, check_safety, convert_date_time
from datetime import datetime
from .Exceptions import *

class Workflow(ServerPrimitive):
    """This class represents an Unicore Workflow.
    """

    def _set_status(self, status):
        if (not status is None):
            check_safety([(status, JobStatus)])
            self.status = status

    def _set_resource_status(self, resource_status):
        if (not resource_status is None):
            check_safety([(resource_status, ResourceStatus)])
            self.resource_status = resource_status

    def _set_storage_id(self, storage_id):
        """Sets the id of the Storage that represents the working directory

        Args:
            storage_id (str): the storage id 
        """
        if (not storage_id is None):
            check_safety([(storage_id, str)])
            self.storage_id = storage_id

    def _set_current_time(self, current_time):
        """Sets the time when the properties of this workflow were updated.

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

    def _set_owner_dn(self, owner_dn):
        if (not owner_dn is None):
            check_safety([(owner_dn, str)])
            self.owner_dn = owner_dn

    def _set_name(self, name):
        if (not name is None):
            check_safety([(name, str)])
            self.name = name

    def update_from_json(self, json):
        # Documented in parent class.
        self._set_status(get_enum_by_str(JobStatus, json['status']))
        self._set_resource_status(
            get_enum_by_str(ResourceStatus, json['resourceStatus'])
        )
        self._set_storage_id(json['storageEPR'].split('=')[-1])
        #TODO rename request time
        self._set_current_time(convert_date_time(json['currentTime']))
        self._set_termination_time(convert_date_time(json['terminationTime']))
        self._set_submission_time(convert_date_time(json['submissionTime']))
        #TODO self._set_acl()
        self._set_owner_dn(json['owner'])
        self._set_name(json['name'])

    def update(self):
        # Documented in parent class.
        self._update(URIs['workflow_sigle_workflow'])

    @ServerPrimitive._check_init
    def get_status(self):
        """Returns the :class:`Constants.JobStatus` of this workflow.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status (:class:`Constants.JobStatus`):  status of this workflow.
        """
        return self.status

    @ServerPrimitive._check_init
    def get_resource_status(self):
        """Returns the :class:`Constants.ResourceStatus` of this workflow.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status (:class:`Constants.ResourceStatus`):  status of this workflow.
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
        """Returns the time when the properties of this workflow were updated.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            current_time: the time of update
        """
        return self.current_time

    @ServerPrimitive._check_init
    def get_termination_time(self):
        """Returns the time when this workflow terminated.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            termination_time: the time when this workflow terminated.
        """
        return self.termination_time

    @ServerPrimitive._check_init
    def get_acl(self):
        """Returns the ACLs of this workflow.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

            .. note:: Due to a lack of Unicore documentation, this method is not
                yet fully implemented.
        
        Returns:
            acl: the ACLs of this workflow
        """
        return self.acl

    @ServerPrimitive._check_init
    def get_owner_dn(self):
        """Returns the DN (distinguished name) of the user owning this workflow.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            dn (str): the DN of the user owning this workflow.
        """
        return self.owner_dn

    @ServerPrimitive._check_init
    def get_submission_time(self):
        """Returns the submission time of this workflow.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            submission_time: the time this workflow has been submitted.
        """
        return self.submission_time

    @ServerPrimitive._check_init
    def get_name(self):
        """Returns the name of this workflow.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            name: the name of this workflow.
        """
        return self.name

    def _reset_init(self):
        """This method is required to reset the state variable that indicates
        if the properties of this Workflow instance have been fetched from the
        Server recently.
        This should only be reset by the WorkflowManager in cases where a change of
        the workflow probperties is expected.
        """
        self.init               = False

    #@ServerPrimitive._check_init
    def __repr__(self):
        return "id: %s, time: %s, status: %s, working_dir: %s." % (
                self.id, 
                self.current_time,
                self.status,
                self.working_dir)

    def __init__(self, id, connection):
        super(Workflow, self).__init__(id)
        self.con                = connection #TODO move into superclass
        self.init               = False
        self.status             = None
        self.resource_status    = None
        self.working_dir        = None
        self.current_time       = None
        self.termination_time   = None
        self.acl                = None
        self.owner_dn           = None
        self.submission_time    = None
        self.name               = None


