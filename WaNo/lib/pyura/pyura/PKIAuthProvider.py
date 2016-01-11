from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from pyura.AuthProvider import AuthProvider
from os import path

class PKIAuthProvider(AuthProvider):
    def __init__(self, private_key, public_cert):
        if (path.exists(private_key) and path.isfile(private_key)):
            self.private_key    = private_key
        else:
            raise ValueError('Private key: Not found or not a file.')

        if (path.exists(public_cert) and path.isfile(public_cert)):
            self.public_cert    = public_cert
        else:
            raise ValueError('Public cert: Not found or not a file.')

    
    def __call__(self, r):
        r.headers
        return r

