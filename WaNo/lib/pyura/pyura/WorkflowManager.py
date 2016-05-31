"""
pyura.WorkflowManager
~~~~~~~~~~~~~~~~
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .Manager import Manager
from .Constants import URIs, JSONKeys, ErrorCodes
from .Workflow import Workflow
from .helpers import check_safety
from .StorageManager import StorageManager

#TODO
# * move _get_id upwards into Manager

  #  Reservation: workflow1234,

  #}

class WorkflowManager(Manager):
    """ The :class:`WorkflowManager.WorkflowManager` controls the life-cycle
    of Workflows on the Unicore Server.

    This includes the creation, (re-)starting, aborting and deleting Workflows.

    .. important::
        Do not instantiate this class directly. You should rather request an
        instance by 

        >>> workflow_manager = pyura.Registry.get_wf_manager()
    """
    def _get_id(self, workflow):
        id = ''
        if (workflow is None or workflow == ''):
            id = self.selected.get_id()
        else:
            if (isinstance(workflow, Workflow)):
                id = workflow.get_id()
            elif (isinstance(workflow, str)):
                id = workflow
            else:
                raise TypeError('Got workflow object of wrong type (%s), ' \
                        'expected %s or %s' % (
                    str(type(workflow)), str(Workflow), str(str)))
        return id

    def _action(self, uri):
        err, resp = self.con.post_uri(uri, '')
        status = resp.status_code

        return (status, err, resp.content)

    def _reset_init(self, workflow):
        """This method is required to reset the state variable that indicates
        if the properties of the given Workflow instance have been fetched from the
        Server recently.
        This should only be reset by the :class:`WorkflowManager.WorkflowManager` in
        cases where a change of the workflow properties is expected.

        Never call this method direct.
        """
        if not workflow is None:
            check_safety([(workflow, Workflow)])
            workflow._reset_init()

    def abort(self, workflow=None):
        """Aborts the execution of a :class:`Workflow.Workflow` on the Unicore server.

        The workflow aborted by this method is either the currently selected workflow or
        any workflow given as optional parameter.

        Args:
            workflow (:class:`Workflow.Workflow`): The workflow to abort or None in oder to abort the currently
            selected one.

        Returns:
            status (int): HTTP status code of the request.

            error (`Constants.ErrorCodes`): Error code in case an error
            occurred, otherwise `Constants.ErrorCodes.NO_ERROR`.

            resp (str): The response of the server. This will contain an empty
            string in most cases.
        """
        id = self._get_id(workflow)
        uri = URIs['workflow_abort'] % id
        self._reset_init(workflow)
        return self._action(uri)

    def update_list(self):
        # Documented in parent class.
        self._update_list(URIs['workflow_list'], JSONKeys['workflow_list'], Workflow)

    def __init__(self, connection):
        super(WorkflowManager, self).__init__(connection)
