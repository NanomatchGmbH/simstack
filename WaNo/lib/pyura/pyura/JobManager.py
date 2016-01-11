"""
pyura.JobManager
~~~~~~~~~~~~~~~~
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from pyura.Manager import Manager
from pyura.Constants import URIs, JSONKeys, ErrorCodes
from pyura.Job import Job
from pyura.helpers import check_safety
from pyura.StorageManager import StorageManager

#TODO
# * move _get_id upwards into Manager

class ReservedResources:
    """This class stores and controls resource reservations for a :class:`Job.Job`.

    A resource reservation, for example, is the amount of memory the Unicore
    server should reserve for a job on every cluster node.
    """

  #Resources: {

  #  # memory per node (bytes, you may use the common "K","M" or "G")
  #  Memory: 2G ,

  #  # walltime (seconds, use "min", "h", or "d" for other units)
  #  Runtime: 86400 ,

  #  # Total number of requested CPUs
  #  CPUs: 64 ,

  #  # you may optionally give the number of nodes
  #  #Nodes: 2 ,
  #  # together with the CPUs per node
  #  #CPUsPerNode: 32,

  #  # Custom resources (site-dependent!)
  #  StackLimitPerThread : 262144,

  #  # Operating system
  #  Operating system: LINUX,   #MACOS, WINNT, ...

  #  # Resource reservation reference
  #  Reservation: job1234,

  #}

    def _set(key, value):
        if key not in self.resources:
            self.resources[key] = ''
        self.resources[key] = value

    def _check_resource(self, resource, check):
        return (not self.cluster_resource is None and check(resource)) \
                or (self.cluster_resource is None)

    def reserve_nodes(self, nodes):
        """ Sets the number of nodes to reserve.

        The resource can not be reserved if this ReservedResources instance was
        initialized with a cluster_resource that now determines the now desired
        value to be invalid.

        Args:
            nodes (int):   number of nodes to reserve.

        Returns:
            True, if successful, False otherwise.
        """
        check = self._check_resource(nodes,
                ClusterResource.check_in_range_nodes)

        if check:
            self._set('Nodes', nodes)

        return check

    def reserve_cpus(self, cpus):
        """ Sets the number of CPUs to reserve.

        The resource can not be reserved if this ReservedResources instance was
        initialized with a cluster_resource that now determines the now desired
        value to be invalid.

        Args:
            cpus (int):   number of CPUs to reserve.

        Returns:
            True, if successful, False otherwise.
        """
        check = self._check_resource(cpus,
                ClusterResource.check_in_range_cpus)

        if check:
            self._set('Nodes', cpus)

        return check

    def reserve_cpus_per_node(self, cpus_per_node):
        """ Sets the number of CPUs to reserve per node.

        The resource can not be reserved if this ReservedResources instance was
        initialized with a cluster_resource that now determines the now desired
        value to be invalid.

        Args:
            cpus_per_node (int):   number of CPUs to reserve per node.

        Returns:
            True, if successful, False otherwise.
        """
        check = self._check_resource(cpus_per_node,
                ClusterResource.check_in_range_cpus_per_node)

        if check:
            self._set('Nodes', cpus_per_node)

        return check

    def reserve_mem_per_node(self, mem_per_node):
        """ Sets the amount of memory per node to reserve.

        The resource can not be reserved if this ReservedResources instance was
        initialized with a cluster_resource that now determines the now desired
        value to be invalid.

        Args:
            mem_per_node (int):   amount of memory per node to reserve

        Returns:
            True, if successful, False otherwise.
        """
        check = self._check_resource(mem_per_node,
                ClusterResource.check_in_range_mem_per_node)

        if check:
            self._set('Nodes', mem_per_node)

        return check

    def get_reservation(self):
        """Returns the resource reservations made.

        Returns:
            the resource reservations made.
        """
        return self.resources

    def __init__(self, cluster_resource=None):
        """Instantiates a new resource reservation object.

        This can be passed to the JobManager.create method in order to assign
        a specific set of cluster resources (CPUs, Nodes, Memory, etc.) to the
        created Job.

        If cluster_resource is passed, all reservations are checked against it.
        This ensures, that only valid reservations are made.

        Args:
            cluster_resource (ClusterResource): Optional argument to check
                resource reservations against.
        """
        self.cluster_resource = cluster_resource
        self.resources = {}

class Imports:
    """This class stores and manages imports that can be assigned to a :class:`Job.Job`.

    An import is a tuple that contains a "from"-path and a "to"-path.
    The "from"-path is the location of the file to upload on the local machine.
    The "to"-path is the location where the uploaded file will be stored on
    the server.
    """

    def _is_in_list(self, rfrom, rto):
        rv = -1
        for i, imp in enumerate(self.imports):
            if imp['From'] == rfrom and imp['To'] == rto:
                rv = i
                break
        return rv


    def add_import(self, rfrom, rto):
        """Adds a file import to the list of imports.

        The method avoids adding duplicates but does not check that files are
        not overwritten on the server side. Even though this creates
        unneccessary trafic, it still might be expected behavior.

        Args:
            rfrom (str):     Path to the file to upload. This might also be a
                server side path (e.g. "u6://DEMO-SITE/Home/testfile")
            rto (str):       Path where to upload the file. This can either be
                relative to the job working directory, the Uspace or a remote
                Uspace.

        Returns:
            (boolean) True, if import has been added, False otherwise.
            The latter occurs when an import with the same source and
            destination has been added
            before.
        """
        rv = False
        if self._is_in_list(rfrom, rto) == -1:
            self.imports.append({
                'From': rfrom,
                'To': rto,
                'FailOnError': True
                })
            rv = True
        return rv

    def remove_import(self, rfrom, rto):
        """Removes a file import rfrom the list of imports that has the same
        source and destination as given by rfrom and to.

        Args:
            rfrom (str):     Path to the file to upload. This might also be a
                server side path (e.g. "u6://DEMO-SITE/Home/testfile")
            rto (str):       Path where to upload the file. This can either be
                relative to the job working directory, the Uspace or a remote
                Uspace.

        Returns:
            True, if import was removed
        """
        i = self._is_in_list(rfrom, rto)
        return not self.imports.pop(i) is None

    def get_imports(self):
        """Returns the list of imports as list of dicts.

        Returns:
            the list of imports as list of dicts.
        """
        return self.imports

    def get_imports_to_upload(self):
        """Returns the list of imports that need to be uploaded to the server.

        Returns:
            the list of imports that need to be uploaded to the server.
        """
        rv = []
        for i in self.imports:
            if not (i['From'].lower().startswith('u6') \
                    or i['From'].lower().startswith('c9m')):
                rv.append(i)
        return rv

    def __init__(self):
        self.imports = []

class JobManager(Manager):
    """ The :class:`JobManager.JobManager` controls the life-cycle of Jobs on the Unicore
    Server.

    This includes the creation, (re-)starting, aborting and deleting Jobs.

    .. important::
        Do not instantiate this class directly. You should rather request an
        instance by 

        >>> job_manager = pyura.Registry.get_job_manager()
    """
    def _get_id(self, job):
        id = ''
        if (job is None or job == ''):
            id = self.selected.get_id()
        else:
            if (isinstance(job, Job)):
                id = job.get_id()
            elif (isinstance(job, str)):
                id = job
            else:
                raise TypeError('Got job object of wrong type (%s), ' \
                        'expected %s or %s' % (
                    str(type(job)), str(Job), str(str)))
        return id

    def _action(self, uri):
        err, resp = self.con.post_uri(uri, '')
        status = resp.status_code

        return (status, err, resp.content)

    def _reset_init(self, job):
        """This method is required to reset the state variable that indicates
        if the properties of the given Job instance have been fetched from the
        Server recently.
        This should only be reset by the :class:`JobManager.JobManager` in
        cases where a change of the job properties is expected.

        Never call this method direct.
        """
        if not job is None:
            check_safety([(job, Job)])
            job._reset_init()

    def start(self, job=None):
        """Starts the execution of a :class:`Job.Job` on the Unicore server.

        The job started by this method is either the currently selected job or
        any job given as optional parameter.

                .. note:: You will have to make sure to upload all required
                    imports first (if any). Otherwise execution will fail.
        

                .. important:: A job must be created (on the server) before it
                    can be started.

        Args:
            job (:class:`Job.Job`): The job to start or None in oder to start the currently
            selected one.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (str): The response of the server. This will contain an empty
            string in most cases.
        """
        # TODO what happens if a job has been started before.
        # TODO should we set a given job as selected?
        id = self._get_id(job)
        uri = URIs['job_start'] % id
        self._reset_init(job)
        return self._action(uri)

    def abort(self, job=None):
        """Aborts the execution of a :class:`Job.Job` on the Unicore server.

        The job aborted by this method is either the currently selected job or
        any job given as optional parameter.

        Args:
            job (:class:`Job.Job`): The job to abort or None in oder to abort the currently
            selected one.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (str): The response of the server. This will contain an empty
            string in most cases.
        """
        id = self._get_id(job)
        uri = URIs['job_abort'] % id
        self._reset_init(job)
        return self._action(uri)

    def restart(self, job=None):
        """Restarts the execution of a :class:`Job.Job` on the Unicore server.

        The job started by this method is either the currently selected job or
        any job given as optional parameter.

        Args:
            job (:class:`Job.Job`): The job to restart or None in oder to 
            restart the currently selected one.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (str): The response of the server. This will contain an empty
            string in most cases.
        """
        id = self._get_id(job)
        uri = URIs['job_restart'] % id
        self._reset_init(job)
        return self._action(uri)

    def delete(self, job=None):
        """Deletes a :class:`Job.Job` on the Unicore server.

        The job deleted by this method is either the currently selected job or
        any job given as optional parameter.

        Args:
            job (:class:`Job.Job`): The job to delete or None in oder to 
            delete the currently selected one.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.
        """
        id = self._get_id(job)
        uri = URIs['job_delete'] % id

        status, err, resp = self.con.delete_uri(uri)
        #TODO what is in resp??

        return (status, err)

    @staticmethod
    def _get_files_to_upload(imports):
        pass

    def upload_imports(self, job, storage_manager, callback=None):
        """Checks the imports of the given :class:`Job.Job` and uploads the required
        import files to the Unicore server.

        This method needs a reference to the current
        :class:`StorageManager.StorageManager` in order
        to upload the files.

        Args:
            job (:class:`Job`):     The :class:`Job` object.

            storage_manager (:class:`StorageManager.StorageManager`): The
            :class:`StorageManager.StorageManager` used to upload the files.

            callback (func): Callback function. For more information on the
            callback *see :func:Connection.put_file()*.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.
        """
        if (job is None
                or storage_manager is None):
            raise ValueError('Parameters must not be None.')

        check_safety([(job, Job), (storage_manager, StorageManager)])
        upload_required, files_to_upload = job.imports_require_upload()

        if upload_required:
            for f in files_to_upload:
                status, err, json = storage_manager.upload_file(
                    f['From'],
                    storage_id=job.get_working_dir(),
                    remote_filename=f['To'],
                    callback=callback
                    )
                if (err != ErrorCodes.NO_ERROR):
                    break
        return (status, err)




    #TODO this should allow the following parameters to be set:
    # * Executable
    # * Arguments
    # * Imports
    def create(
            self,
            executable,
            arguments=None,
            imports=None,
            environment=None,
            resources=None
        ):
        """Creates a job object remote and returns a representation of the object.

        By default, jobs are **not** started automatically.
        Instead, :func:`JobManager.start` must be used.

        Args:
            executable (str):   The executable

            arguments (str):    Arguments that are passed to the executable on
            the command line.

            imports (:class:`JobManager.Imports`): Files to import

            environment ([str]): List of environment variable assignments. The
            list should contain entries in the form "ENV_VAR=bar"
            resources

            resources (:class:`JobManager.ReservedResources`): Resource
            reservations for the Job.


        Returns:
            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            job (:class:`Job.Job`): Representation of the newly created job on the server.
            This will be None in an error case.
        """
        #TODO check arguments
        #TODO check if imports require file upload. If one import does, set
        # to true and upload files after job creation.
        # _get_files_to_upload(imports)

        #haveClientStageIn = False
        #TODO swap
        haveClientStageIn = True

        jsonjob = {
                JSONKeys['job_executable']:         executable,
            }
        jsonjob[JSONKeys['job_client_stage_in']] =  haveClientStageIn

        if not arguments is None:
            jsonjob[JSONKeys['job_arguments']] =        arguments
        if not imports is None:
            jsonjob[JSONKeys['job_imports']] =          imports.get_imports()
        if not environment is None:
            jsonjob[JSONKeys['job_environment']] =      environment
        if not resources is None:
            jsonjob[JSONKeys['job_resources']] =        resources

        return self._create(URIs['job_create'], jsonjob, Job,
                {'imports': imports}
            )

    def create_app(
            self,
            application,
            parameters=None,
            imports=None,
            environment=None,
            resources=None
        ):
        """Creates an application job object remote and returns a
        representation of the object.

        Instead of executing an arbitrary command as done by
        :func:`JobManager.create`, this method executes a server-side
        application.

        By default, jobs are **not** started automatically.
        Instead, :func:`JobManager.start` must be used.

        Args:
            executable (str):   The executable

            arguments (str):    Arguments that are passed to the executable on
            the command line.

            imports (:class:`JobManager.Imports`): Files to import

            environment ([str]): List of environment variable assignments. The
            list should contain entries in the form "ENV_VAR=bar"
            resources

            resources (:class:`JobManager.ReservedResources`): Resource
            reservations for the Job.

        Returns:
            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            job (:class:`Job.Job`): Representation of the newly created job on the server.
            This will be None in an error case.
        """
        #TODO this can not simply be mapped to create, we need different json
        # keys for application name, etc...
        #TODO check arguments
        #TODO check if imports require file upload. If one import does, set
        # to true and upload files after job creation.
        return self.create(
                application.get_name(),
                arguments = parameters,
                imports = imports,
                environment = environment,
                resources = resources
                )

    #def _init_primitive(self, id):

    def update_list(self):
        # Documented in parent class.
        self._update_list(URIs['job_list'], JSONKeys['job_list'], Job)

    def __init__(self, connection):
        super(JobManager, self).__init__(connection)
