from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import unittest
import logging

from JobManagerTestSuite import JobManagerTestSuite
from UnittestBundledTests import Bundle, BundleRunner
from ConnectionTestSuite import ConnectionTestSuite

verbosity=0


if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger('pyura')
    #logger.setLevel(10)
    suites = []

    suites.append(Bundle('Connection')\
            .add_suite(ConnectionTestSuite.get_test_suite()))
    #suites.append(Bundle('Job / JobManager')\
    #        .add_suite(JobManagerTestSuite.get_test_suite()))

    BundleRunner(verbosity=verbosity).run(suites)
