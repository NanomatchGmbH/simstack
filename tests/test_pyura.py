from __future__ import print_function
import unittest

class PyuraTests(unittest.TestCase):
    def setup(self):
        print("This function will be called before each test")
    
    def teardown(self):
        print("This function will be called after each test")

    @classmethod
    def setup_class(cls):
        print("This method is called before all tests")

    def test_enum(self):
        from pyura.Constants import Constants as uc
        assert(uc.JobStatus.QUEUED != uc.JobStatus.FAILED)

    @classmethod
    def teardown_class(cls):
        print("Called at the end")
        
