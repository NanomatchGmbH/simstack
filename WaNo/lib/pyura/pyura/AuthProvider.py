from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from requests.auth import AuthBase

class AuthProvider(AuthBase):
    """Abstract authentication provider"""

    def get_hash(self):
        raise NotImplementedError(
                "This method must be implemented in child class."
            )

    def __init__(self):
        pass
