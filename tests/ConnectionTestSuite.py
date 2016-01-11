from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import lib.mock as mock
import lib.httpretty as httpretty
import json

from pyura.Connection import Connection
from pyura import HTTPBasicAuthProvider
from pyura import ErrorCodes, HTTPStatusCodes
from tests.FakeRequestResponses import RESP_BASE
import requests


class ConnectionTest(unittest.TestCase):
    def setUp(self):
        self.auth_provider=HTTPBasicAuthProvider('user', 'password')
        self.base_uri = 'http://kit.edu'
        httpretty.HTTPretty.allow_net_connect = False

    def tearDown(self):
        pass

    def test_set_auth_provider(self):
        con = Connection()
        # first, set auth provider to something invalid, but similar on first
        # sight:
        auth_provider = ('user', 'password')

        self.assertRaises(TypeError, con.set_auth_provider,
                {'auth_provider': auth_provider})
        self.assertIsNone(con.get_auth_provider())

        # Try to set it to None. This should not change anythin, since it is
        # None already
        con.set_auth_provider(None)
        self.assertIsNone(con.get_auth_provider())

        # Now, set it to something usefull
        auth_provider = self.auth_provider
        try:
            con.set_auth_provider(auth_provider)
        except Exception as e:
            self.fail("Caught unexpected exception.")

        # check that it did what we expected
        self.assertEqual(con.get_auth_provider(), auth_provider)
        self.assertEqual(con.get_auth_provider().username, auth_provider.username)
        self.assertEqual(con.get_auth_provider().password, auth_provider.password)

        # set it back to None, theres one more thing to test
        con.set_auth_provider(None)
        self.assertIsNone(con.get_auth_provider())
        try:
            con = Connection(auth_provider=self.auth_provider)
        except Exception as e:
            self.fail("Caught unexpected exception.")
        self.assertEqual(con.get_auth_provider(), auth_provider)
        self.assertEqual(con.get_auth_provider().username, auth_provider.username)
        self.assertEqual(con.get_auth_provider().password, auth_provider.password)

    def _connect_callback(self, client):
        self.assertFalse(client is None)
        self.assertTrue('dn' in client)
        self.assertTrue('xlogin' in client)
        self.callback_executed = True

    @staticmethod
    def _connection_timeout(request, uri, headers):
        raise requests.exceptions.ReadTimeout('Connection timeout.')

    @staticmethod
    def _connection_abort(request, uri, headers):
        raise requests.exceptions.ConnectionError('Connection aborted.')

    @httpretty.activate
    def test_connect(self):
        uri = self.base_uri

        con = Connection(base_uri=uri,
                auth_provider=self.auth_provider)

        httpretty.register_uri(httpretty.GET, uri,
                body=json.dumps(RESP_BASE),
                content_type="application/json",
                status=200
                )

        # test simple sucessfull connect
        self.assertFalse(con.is_connected())
        err, status_code = con.connect()
        self.assertTrue(con.is_connected())
        self.assertEqual(err, ErrorCodes.NO_ERROR)
        self.assertEqual(status_code, HTTPStatusCodes.OK)

        # a reconnect should not change anything
        err, status_code = con.connect()
        self.assertTrue(con.is_connected())
        self.assertEqual(err, ErrorCodes.NO_ERROR)
        self.assertEqual(status_code, HTTPStatusCodes.OK)

        # testing callback
        con = Connection(base_uri=uri,
                auth_provider=self.auth_provider,
                user_callback=self._connect_callback)
        self.callback_executed = False
        err, status_code = con.connect()
        self.assertTrue(self.callback_executed)
        self.assertEqual(err, ErrorCodes.NO_ERROR)
        self.assertEqual(status_code, HTTPStatusCodes.OK)

        httpretty.reset()

    @httpretty.activate
    def test_disconnect(self):
        uri = self.base_uri

        con = Connection(base_uri=uri,
                auth_provider=self.auth_provider)

        httpretty.register_uri(httpretty.GET, uri,
                body=json.dumps(RESP_BASE),
                content_type="application/json",
                status=200
                )
        
        # connect first
        err, status_code = con.connect()
        self.assertTrue(con.is_connected())
        self.assertEqual(err, ErrorCodes.NO_ERROR)
        self.assertEqual(status_code, HTTPStatusCodes.OK)

        # disconnect
        #       also try to disconnect while not being connected
        for i in range(0,2):
            dis = con.disconnect()
            self.assertTrue(dis)
            self.assertFalse(con.is_connected())

    @httpretty.activate
    def test_open_uri(self):
        uri = self.base_uri

        con = Connection(base_uri=uri,
                auth_provider=self.auth_provider)

        # test successful request
        httpretty.register_uri(httpretty.GET, uri,
                body=json.dumps(RESP_BASE),
                content_type="application/json",
                status=200)

        con.connect()
        self.assertTrue(con.is_connected())
        status, err, resp = con.open_uri('')

        # test error codes: 404
        httpretty.reset()
        httpretty.register_uri(httpretty.GET, uri,
                body=json.dumps(RESP_BASE),
                content_type="application/json",
                status=404)
        status, err, resp = con.open_uri('')
        self.assertEqual(err, ErrorCodes.HTTP_ERROR)
        self.assertEqual(status, HTTPStatusCodes.Not_Found)

        # test error codes: 500
        httpretty.reset()
        httpretty.register_uri(httpretty.GET, uri,
                body=json.dumps(RESP_BASE),
                content_type="application/json",
                status=500)
        status, err, resp = con.open_uri('')
        self.assertEqual(err, ErrorCodes.HTTP_ERROR)
        self.assertEqual(status, HTTPStatusCodes.Internal_Server_Error)

        # test timeout
        httpretty.reset()
        httpretty.register_uri(httpretty.GET, uri,
                body=ConnectionTest._connection_timeout
                )
        status, err, resp = con.open_uri('')
        self.assertEqual(err, ErrorCodes.REQ_TIMEOUT)
        self.assertEqual(status, HTTPStatusCodes.INVALID_STATUS)

        # test broken uri
        httpretty.reset()
        httpretty.register_uri(httpretty.GET, uri,
                body=ConnectionTest._connection_abort)
        status, err, resp = con.open_uri('')
        self.assertEqual(err, ErrorCodes.CONN_ERROR)
        self.assertEqual(status, HTTPStatusCodes.INVALID_STATUS)

        # test, if an uri is appended and requested correctly
        httpretty.reset()
        sub_uri = 'append_this'
        httpretty.register_uri(httpretty.GET, uri,
                body=json.dumps(RESP_BASE),
                content_type="application/json",
                status=200)
        status, err, resp = con.open_uri(sub_uri)
        self.assertEqual(httpretty.last_request().path, '/%s' % sub_uri)





class ConnectionTestSuite:
    @classmethod
    def get_test_suite(self):
        return unittest.TestLoader().loadTestsFromTestCase(ConnectionTest)
