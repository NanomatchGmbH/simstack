from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .helpers import check_safety
import types
from .ConnectionManager import ConnectionManager
import logging
from .AuthProvider import AuthProvider
from .User import User
import inspect
from .JobManager import JobManager
from .StorageManager import StorageManager
from .SiteManager import SiteManager
from .Constants import ErrorCodes, ConnectionState

class Registry:
    """Representation of a Unicore Registry.
    """

    def _inspector(self, funct, error, status_code):
        if not inspect.getargspec(funct).args is None:
            mykwargs = {}
            args = inspect.getargspec(funct).args
            if 'calling_object' in args:
                mykwargs['calling_object'] = self
            if 'status_code' in args:
                mykwargs['status_code'] = status_code
            if 'error_code' in args:
                mykwargs['error_code'] = error
            funct(**mykwargs)
        else:
            funct()


    def set_auth_provider(self, auth_provider):
        """Sets the authentication provider.

        Args:
            auth_provider: the authentication provider.
        """
        self.auth_provider     = auth_provider
    
    def set_base_uri(self, base_uri):
        """Sets the base URI of the Unicore Server.

        This will most likely be of the form 
        "'https://HOSTNAME[:PORT]/SITE/rest/core"

        Args:
            base_uri (str): the base uri of the server.
        """
        self.base_uri = base_uri


    def _set_managers(self):
        self.job_manager        = JobManager(self.connection_manager.get_job_connection())
        self.storage_manager    = StorageManager(self.connection_manager.get_storage_connection())
        self.site_manager       = SiteManager(self.connection_manager.get_site_connection())

    def _unset_managers(self):
        #TODO do not setup Managers here, they need their respective connection.
        self.job_manager        = None
        self.storage_manager    = None
        self.site_manager       = None

        self.logger.info('Registry set up.')
        

    #TODO more listener/callback functions:
    # * connected()
    # * disconnected()
    # * ...
    #
    # connected() should for example be called from connect()
    # after establishing the connection and calling the callback passed
    # in the function.
    # 
    #    def set_connection_listener():

    def set_workflow_base_uri(self, uri):
        if not uri is None and uri != "":
            self.connection_manager.set_workflow_base_uri(uri)
            return True
        return False

    def connect(self, callback=None):
        """Connects to the Registry.

        This method must be called prior to any further usage of the API.

        The method accepts a function as additional parameter which is called
        after successfully establishing the connection.
        The callback function **must** have the following parameters with the
        exact names in its signature (method name itself is arbitrary):

        >>> callback_method(self, error_code, status_code)

        Args:
            callback (function): (optional) callback function

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.
        """
        err = ErrorCodes.NO_ERROR
        sc = 200

        # set registry base uri again, just to be shure not to miss any changes.
        self.connection_manager.set_registry_base_uri(self.base_uri)

        #TODO check connection state
        err, con_status = self.connection_manager.connect(
                self.auth_provider, self._user_callback)

        if (not callback is None):
            check_safety([(callback, types.FunctionType)])
            self._inspector(callback, error_code, status_code)
            callback(error_code=err, status_code=con_status)

        if err == ErrorCodes.NO_ERROR and con_status == ConnectionState.CONNECTED:
            self._set_managers()

        return (err, con_status)
        
    def update(self, callback=None):
        """Updates all managers.

        This method updates all managers associated with the currently connected
        Registry of Unicore Objects which includes the managers for 
        Sites, Storages and Jobs.

        The method accepts a function as additional parameter which is called
        after successfully establishing the connection.
        The callback function **must** have the following parameters with the
        exact names in its signature (method name itself is arbitrary):

        >>> callback_method(self, error_code, status_code)

        Args:
            callback (function): (optional) callback function

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.
        """
        err = ErrorCodes.NO_ERROR
        sc = 200
        if (not callback is None):
            check_safety([(callback, types.FunctionType)])

        #TODO check connection state
        #TODO
        pass

    def get_base_uri(self):
        return self.connection_manager.get_registry_base_uri()

    def get_auth_provider_hash(self):
        return self.con.get_auth_provider_hash()
    
    def get_user(self):
        """Returns a :class:`User.User` object representing the Unicore user.

        Returns:
            user (:class:`User.User`): the Unicore user.
        """
        return self.user

    def get_job_manager(self):
        """Returns the :class:`JobManager.JobManager`.

        Returns:
            job_manager (:class:`JobManager.JobManager`): the job manager
        """
        return self.job_manager

    def get_storage_manager(self):
        """Returns the :class:`StorageManager.StorageManager`.

        Returns:
            job_manager (:class:`StorageManager.StorageManager`): the job manager
        """
        return self.storage_manager

    def get_site_manager(self):
        """Returns the :class:`SiteManager.SiteManager`.

        Returns:
            job_manager (:class:`SiteManager.SiteManager`): the job manager
        """
        return self.site_manager
    
    def _user_callback(self, json_user):
        #TODO error handling
        self.user = User(
                json_user['dn'],
                json_user['xlogin']['UID'],
                json_user['role']['selected'],
                json_user['xlogin']['availableUIDs'],
                json_user['role']['availableRoles']
                )
        
        
    def __init__(self, base_uri=None, auth_provider=None):
        self.logger = logging.getLogger('pyura')

        self.base_uri           = base_uri
        self.connection_manager = ConnectionManager(base_uri=base_uri)
        self.auth_provider      = auth_provider

    def __str__(self):
        return self.base_uri
