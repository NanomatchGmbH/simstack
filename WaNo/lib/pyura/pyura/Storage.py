from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .ServerPrimitive import ServerPrimitive
from functools import wraps

class Storage(ServerPrimitive):
    """This class represents a Unicore Storage.
    """

    def _set_metadata_support(self, has_metadata_support):
        if (not has_metadata_support is None):
            check_safety([has_metadata_support, bool])
            self.metadata_supported = has_metadata_support

    def _set_resource_status(self, resource_status):
        if (not resource_status is None):
            check_safety([(resource_status, ResourceStatus)])
            self.resource_status = resource_status

    def _set_description(self, description):
        if (not description is None):
            check_safety([(description, str)])
            self.description = description

    def _set_current_time(self, current_time):
        if (not current_time is None):
            check_safety([(current_time, datetime)])
            self.current_time = current_time

    def _set_termination_time(self, termination_time):
        if (not termination_time is None):
            check_safety([(termination_time, datetime)])
            self.termination_time = termination_time

    def _set_umask(self, umask):
        if (not umask is None):
            check_safety([(umask, int)])
            self.umask = umask

    def _set_acl(self, acl):
        if (not acl is None):
            check_safety([(acl, str)])
            self.acl = acl

    def _set_owner(self, owner):
        if (not owner is None):
            check_safety([(owner, str)])
            self.owner = owner

    def _set_mount_point(self, mount_point):
        if (not mount_point is None):
            check_safety([(mount_point, str)])
            self.mount_point = mount_point

    def _set_protocols(self, protocols):
        if (not protocols is None):
            check_safety([(protocols, [Protocols])])
            self.protocols = protocols


    @ServerPrimitive._check_init
    def get_has_metadata_support(self):
        """Returns the metadata support  of this storage.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status:  metadata support status of this storage.
        """
        return self.has_metadata_supported

    @ServerPrimitive._check_init
    def get_resource_status(self):
        """Returns the :class:`Constants.ResourceStatus` of this storage.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status (:class:`Constants.ResourceStatus`):  status of this storage.
        """
        return self.resource_status

    @ServerPrimitive._check_init
    def get_description(self):
        """Returns the description of this storage.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            status (str):  description of this storage.
        """
        return self.description

    @ServerPrimitive._check_init
    def get_current_time(self):
        """Returns the time when the properties of this storage were updated.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            current_time: the time of update
        """
        return self.current_time

    @ServerPrimitive._check_init
    def get_termination_time(self):
        """Returns the time when this storage terminated.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            termination_time: the time when this storage terminated.
        """
        return self.termination_time

    @ServerPrimitive._check_init
    def get_umask(self):
        """Returns the umask used for files in this storage.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            umask: the umask used for files in this storage.
        """
        return self.umask

    @ServerPrimitive._check_init
    def get_acl(self):
        """Returns the ACLs of this storage.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.

            .. note:: Due to a lack of Unicore documentation, this method is not
                yet fully implemented.
        
        Returns:
            acl: the ACLs of this storage
        """
        return self.acl

    @ServerPrimitive._check_init
    def get_owner(self):
        """Returns the DN (distinguished name) of the user owning this storage.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            dn (str): the DN of the user owning this storage.
        """
        return self.owner

    @ServerPrimitive._check_init
    def get_mount_point(self):
        """Returns the mount point where this storage is mounted.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            mount point: mount point of this storage.
        """
        return self.mount_point

    @ServerPrimitive._check_init
    def get_protocols(self):
        """Returns the :class:`Constants.Protocols` supported by this storage.

        This method will query the information from the remote server if
        necessary. Therefore, this method might not return immediately.
        
        Returns:
            protocols (:class:`Constants.Protocols`): supported protocols.
        """
        return self.protocols

    def update_from_json(self, json):
        # Documented in parent class.
        self._set_metadata_support(json['metadataSupported'])
        self._set_resource_status(json['resourceStatus'])
        self._set_description(json['description'])
        self._set_current_time(convert_date_time(json['currentTime']))
        self._set_termination_time(convert_date_time(json['terminationTime']))
        #TODO try catch
        self._set_umask(int(json['umask']))
        #self._set_acl(json['acl'])
        self._set_owner(json['owner'])
        self._set_mount_point(json['mount_point'])
        self._set_protocols(get_enums_by_strs(Protocols, json['protocols']))

    def update(self):
        # Documented in parent class.
        self._update(URIs['storages_single_storage'])

    def __init__(self, id, connection=None):
        super(Storage, self).__init__(id)
        self.con                = connection
        self.metadata_supported = False
        self.resource_status    = None
        self.description        = None
        self.termination_time   = None
        self.umask              = None
        self.acl                = None
        self.owner              = None
        self.mount_point        = None
        self.protocols          = None

