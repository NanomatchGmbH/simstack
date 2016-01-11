from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import lib.mock as mock

from pyura import Job
from pyura import Connection

class JobTest(unittest.TestCase):
    def test_setters(self):
        connection = mock.create_autospec(Connection)

class JobManagerTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_faketest(self):
        assert(True == True)

    def test_me_fails(self):
        assert(True == False)

    #def __init__(self):
    #    pass

class JobManagerTestSuite():
    @classmethod
    def get_test_suite(self):
        jobsuite = unittest.TestLoader().loadTestsFromTestCase(JobTest)
        jobmanagersuite = unittest.TestLoader().loadTestsFromTestCase(JobManagerTest)

        return [jobsuite, jobmanagersuite]
