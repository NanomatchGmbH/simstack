from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from .AuthProvider import AuthProvider
from requests.auth import HTTPBasicAuth
from hashlib import md5

class HTTPBasicAuthProvider(HTTPBasicAuth, AuthProvider):
    def get_hash(self):
        return self.auth_hash

    def __init__(self, username, password):
        super(HTTPBasicAuthProvider, self).__init__(username, password)
        self.auth_hash = md5(str("%s%s" % (username, password)).encode('utf-8'))

    def __call__(self, r):
#        print type(r)
#        print r
        return super(HTTPBasicAuthProvider, self).__call__(r)
