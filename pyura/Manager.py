"""
pyura.Manager
~~~~~~~~~~~~~
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from pyura.helpers import is_in_list, check_safety
from pyura.Constants import URIs, ErrorCodes
from pyura.ServerPrimitive import ServerPrimitive
from pyura.Connection import Connection

class Manager(object):
    """Abstract class that represents a common interface for a Manager.
    .. warning:: Do not instantiate directly.
    """

    def set_connection(self, con):
        """Sets the :class:`Connection.Connection` used by this Manager.

        Args:
            con (:class:`Connection.Connection`): the connection to be used by
            this manager.
        """
        if (not con is None):
            check_safety([(con, Connection)])
            self.con = con

    def select(self, primitive):
        """Selects a server primitive.

        Args:
            primitive (:class:`ServerPrimitive.ServerPrimitive`): the primitive
            to select.
        """
        if (not primitive is None
                #TODO does this have to be overwritten by each Manager
                # in order to check against the correct ServerPrimitive?
                and check_safety([(primitive, ServerPrimitive)])
                and is_in_list(self.list, primitive)
                ):
            self.selected = primitive
    
    def _select_default(self):
        if (len(self.list) > 0):
            self.select(self.list[0])

    def get_selected(self):
        """Returns the currently selected ServerPrimitive.

        Returns:
            the currently selected ServerPrimitive.
        """
        return self.selected


    def _update_list(self, uri, key, server_primitive):
        status, err, resp = self.con.open_json_uri(uri)
        if (status == 200
                and err == ErrorCodes.NO_ERROR
                and key in resp
            ):
            self.list = []
            for e in resp[key]:
                primitive = server_primitive(
                    server_primitive.get_id_from_uri(e),
                    self.con
                )
                if (not primitive is None):
                    self.list.append(primitive)
            #TODO what if a different primitive has been selected before calling
            # the update method?
            # should we remember the selection? this would be more intuitive, but
            # what if the primitive has been deleted?!
            self._select_default()
        else:
            #TODO what now?
            pass

    def update_list(self):
        """Updates the list of ServerPrimitives from the remote server.
        """
        raise NotImplementedError("This method must be overwritten by child " \
                "classes.")
        
    def _create(self, uri, jsondata, server_primitive, primitive_args={}):
        status, err, resp = self.con.post_json(uri, jsondata)
        rv = None

        if (status >= 200 and status < 300
                and err == ErrorCodes.NO_ERROR):
            id = server_primitive.get_id_from_uri(resp.headers['location'])
            rv = server_primitive(id, self.con, **primitive_args)
        else:
            #TODO ?! What kind of errors can occur here? (beside of HTTP errors)
            print("ERROR: status: %d, error: %s,\nRESP\n%s" % (status, err, resp.content))
            pass

        #TODO Should we select() the new primitive?
        return err, rv


    def create(self):
        raise NotImplementedError("This method must be overwritten by child " \
                "classes.")

    def delete(self):
        raise NotImplementedError("This method must be overwritten by child " \
                "classes.")

    def get_by_id(self, id):
        """Returns a ServerPrimitive if the given id identifies one in the 
        list of ServerPrimitive held by this Manager. If the id matches no
        item in the list, None is returned.

        Note:
            This requires the list to be initialized by calling update().

        Args:
            id (int): the id of the ServerPrimitive to return.

        Returns:
            ServerPrimitive: a ServerPrimitive with the given id, None if not
                found.
        """
        rv = None
        if (not id is None and check_safety([(id, str)])):
            for p in self.list:
                if (p.get_id() == id):
                    rv = p
                    break
        return rv

    def get_list(self):
        """Returns the list of ServerPrimitives held by this Manager.

        Returns:
            the list of ServerPrimitives hold by this Manager.
        """
        return self.list
        
    def __init__(self, connection):
        #self.con        = connection
        self.set_connection(connection)
        self.selected   = None
        self.list       = []
        #NOTE: this can not work, since Connection.connect has maybe not been
        # called yet.
        #self.update_list()

