from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from pyura.ServerPrimitive import ServerPrimitive
from pyura.Application import Application
from datetime import datetime
from pyura.helpers import get_enum_by_str, check_safety, convert_date_time
from pyura.Constants import URIs, ResourceStatus
from pyura.ClusterResource import ClusterResources

class Site(ServerPrimitive):
    """Represents an Unicore Server Site.
    """

    def _set_resource_status(self, resource_status):
        if (not resource_status is None):
            check_safety([(resource_status, ResourceStatus)])
            self.resource_status = resource_status

    def _set_other_info(self, other_info):
        if (not other_info is None):
            check_safety([(other_info, dict)])
            self.other_info = other_info

    def _set_termination_time(self, termination_time):
        if (not termination_time is None):
            check_safety([(termination_time, datetime)])
            self.termination_time = termination_time

    def _set_current_time(self, current_time):
        if (not current_time is None):
            check_safety([(current_time, datetime)])
            self.current_time = current_time

    def _set_umask(self, umask):
        if (not umask is None):
            check_safety([(umask, str)])
            self.umask = umask

    def _set_acl(self, acl):
        if (not acl is None):
            check_safety([(acl, str)])
            self.acl = acl

    def _set_owner_dn(self, owner):
        if (not owner is None):
            check_safety([(owner, str)])
            self.owner_dn = owner

    def _set_applications(self, applications):
        if (not applications is None):
            check_safety([(applications, [Application])])
            self.applications = applications

    def _set_number_of_jobs(self, number_of_jobs):
        if (not number_of_jobs is None):
            check_safety([(number_of_jobs, int)])
            self.number_of_jobs = number_of_jobs

    def _set_storages(self, storages):
        if (not storages is None):
            check_safety([(storages, [str])])
            self.storages = storages

    def _set_resources(self, resources):
        if (not resources is None):
            check_safety([(resources, ClusterResources)])
            self.resources = resources

    def _set_supports_reservation(self, supports_reservation):
        if (not supports_reservation is None):
            check_safety([(supports_reservation, bool)])
            self.supports_reservation = supports_reservation

    def update_from_json(self, json):
        # Documented in parent class.
        self._set_resource_status(
            get_enum_by_str(ResourceStatus, json['resourceStatus'])
        )
        self._set_other_info(json['otherInfo'])
        self._set_termination_time(convert_date_time(json['terminationTime']))
        self._set_current_time(convert_date_time(json['currentTime']))
        self._set_umask(json['umask'])
        #TODO self._set_acl(json['acl'])
        self._set_owner_dn(json['owner'])
        self._set_number_of_jobs(json['numberOfJobs'])
        self._set_supports_reservation(
                [False, True][json['supportsReservation'].lower() == "true"])

        self._set_resources(ClusterResources(json['resources']))

        apps = []
        for app in json['applications']:
            apps.append(Application(*(app.split('---'))))
        self._set_applications(apps)

        storages = []
        for storage in json['storages']:
            storages.append(ServerPrimitive.get_id_from_uri(storage))
        self._set_storages(storages)

    def update(self):
        # Documented in parent class.
        self._update(URIs['sites_single_site'])

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
    def get_other_info(self):
        """Returns a JSON object containing additional information about the
        site.

        .. note:: There is no documentation what this realy contains.
            It will probably be empty.

        Returns:
            otherInfo (JSON): additional information about the site.
        """
        return self.other_info

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
    def get_current_time(self):
        """Returns the time when the properties of this job were updated.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

        Returns:
            current_time: the time of update
        """
        return self.current_time

    @ServerPrimitive._check_init
    def get_umask(self):
        return self.umask

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
    def get_owner_dn(self):
        """Returns the DN (distinguished name) of the user owning this job.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

        Returns:
            dn (str): the DN of the user owning this job.
        """
        return self.owner_dn

    @ServerPrimitive._check_init
    def get_applications(self):
        """Returns the list of :class:`Application.Application` provided by the
        server.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

        Returns:
            applications (:class:`Application.Application`): list of applications
        """
        return self.applications

    @ServerPrimitive._check_init
    def get_number_of_jobs(self):
        """Returns the number of jobs available to the user.

        The total number of jobs available on the site migth be larger than
        what is returned by this method but is not available to the user.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

        Returns:
            jobs (int): number of jobs available on the site to the user.
        """
        return self.number_of_jobs

    @ServerPrimitive._check_init
    def get_storages(self):
        """Returns a list of storages available on the site to the user.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

        Returns:
            storages ([str]): list of storages
        """
        return self.storages

    @ServerPrimitive._check_init
    def get_resources(self):
        """Returns a :class:`ClusterResource.ClusterResources` representation of
        the server's recources.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

        Returns:
            resources (:class:`ClusterResource.ClusterResources`): the server's
            resources.
        """
        return self.resources

    @ServerPrimitive._check_init
    def get_supports_reservation(self):
        """Returns True, if the server supports resource reservations, false
        otherwise.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

        Returns:
            support (boolean): true, if the server supports reservations.
        """
        return self.supports_reservation

    def __init__(self, id, connection=None):
        super(Site, self).__init__(id)
        self.con                    = connection
        self.resource_status        = None
        self.other_info             = None
        self.termination_time       = None
        self.current_time           = None
        self.umask                  = None
        self.acl                    = None
        self.owner_dn               = None
        self.applications           = None
        self.number_of_jobs         = None
        self.storages               = None
        self.resources              = None
        self.supports_reservation   = None
        self.init                   = False
