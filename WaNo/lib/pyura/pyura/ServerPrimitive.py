from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from functools import wraps
from pyura.Constants import ErrorCodes
from pyura.Exceptions import DeletedResourceRequested

class ServerPrimitive(object):
    """Abstract class that represents a common interface for a Unicore
    server primitive.

    Server primitives are, for example, jobs, storages, sites, etc.
    """


    def __init__(self, id):
        """Instantiates a new ServerPrimitive object.

        Args:
            id (str): the Unicore ID of the object.
        """
        self.id = id

    def get_id(self):
        """Returns the Unicore ID of this ServerPrimitive.

        Returns:
            id (str): the Unicore ID of this ServerPrimitive.
        """
        return self.id

    def equals(self, other):
        """Checks, if a given instance equals this ServerPrimitive.

        Returns:
            true, if both instances are equal.
        """
        rv = false
        try:
            check_safety((other, ServerPrimitive))
            rv = (self.id == other.get_id())
        except:
            pass

        return rv

    def _update(self, uri):
        sc, err, json = self.con.open_json_uri(uri % self.id)
        if (sc == 200 and err == ErrorCodes.NO_ERROR):
            self.update_from_json(json)
            self.init = True
        else:
            raise DeletedResourceRequested("Request to %s returned %d", (
                uri % self.id,
                sc
            ))


    def update_from_json(self, json):
        """Updates this ServerPrimitive from the given JSON representation of
        the ServerPrimitive.

        Args:
            json (json, dict): JSON representation of the ServerPrimitive.
        """
        raise NotImplementedError("This method must be overwritten by child " \
                "classes.")

    def update(self):
        """Fetches new information on this ServerPrimitive from remote and
        updates it.
        """
        raise NotImplementedError("This method must be overwritten by child " \
                "classes.")

    @staticmethod
    def get_id_from_uri(uri):
        """ Extracts an Unicore ID of a ServerPrimitive's URI.

        Returns:
            id (str): the extracted ID.
        """
        return uri.split('/')[-1]

    @classmethod
    def _check_init(cls, f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            if not self.init:
                self.update()
            return f(self, *args, **kwargs)
        return wrapper
