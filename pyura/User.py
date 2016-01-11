from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .helpers import check_safety

class User:
    """Representation of an Unicore User.
    """

    def __init__(self, dn, uid, role, avail_groups, avail_rols):
        check_safety([
            (dn, str),
            (uid, str),
            (role, str),
            (avail_groups, [str]),
            (avail_rols, [str])])
        self.dn             = dn
        self.uid            = uid 
        self.role           = role
        self.avail_rols     = avail_rols
        self.avail_groups   = avail_groups
        
    """Returns the user's DN.

    Returns:
        (str)       the user's DN.
    """
    def get_dn(self):
        return self.dn

    """Returns the user's UID.

    Returns:
        (str)       the user's UID.
    """
    def get_uid(self):
        return self.uid

    """Returns the user's role(s).

    Returns:
        ([str])     the user's role(s).
    """
    def get_role(self):
        return self.role

    """Returns the list of available roles.

    Returns:
        ([str])     the list of available roles.
    """
    def get_available_roles(self):
        return self.avail_rols

    """Returns the list of available groups.

    Returns:
        ([str])     the list of available groups.
    """
    def get_available_groups(self):
        return self.avail_groups

    def __str__(self):
        return '<%s, %s>' % (self.uid, self.dn)
