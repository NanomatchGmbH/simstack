from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import unittest
import time
import sys

class BundledSuite(unittest.TestSuite):
    name = "BundledSuite"

class Bundle:
    def get_name(self):
        return self.name

    def get_suites(self):
        return self.suites

    def add_suite(self, testsuite):
        self.suites.extend(testsuite)
        return self

    def __init__(self, name):
        self.suites = []
        self.name = name

class BundledTextTestResult(unittest.TextTestResult):
    def add_result(self, result):
        self.failfast       = False or result.failfast
        self.testsRun       = self.testsRun + result.testsRun
        self.failures.extend(result.failures)
        self.errors.extend(result.errors)
        self.skipped.extend(result.skipped)
        self.expectedFailures.extend(result.skipped)
        self.unexpectedSuccesses.extend(result.skipped)
        self.shouldStop = False or result.shouldStop
        self.buffer = False or result.buffer

    def __init__(self, stream, descriptions, verbosity, result=None):
        super(BundledTextTestResult, self)\
                .__init__(
                        stream,
                        descriptions,
                        verbosity
                        )
        if not result is None:
            self.add_result(result)


class BundleRunner(unittest.TextTestRunner):
    def __init__(self,
                stream=sys.stderr, descriptions=True, verbosity=1,
                failfast=False, buffer=False
        ):
        super(BundleRunner, self)\
                .__init__(stream, descriptions, verbosity, failfast, buffer,
                resultclass=BundledTextTestResult
                )

    @staticmethod
    def _s(n):
        return n != 1 and "s" or ""

    def print_result(self, result, timeTaken, message):
        self.stream.writeln(message)
        run = result.testsRun
        errors = len(result.errors)
        failures = len(result.failures)
        skipped = len(result.skipped)
        success = run - (errors + failures + skipped)

        self.stream.writeln("Ran %d test%s in %.3fs: "\
                "%d successful, %d error%s, %d failure%s, %d skipped" %
                            (run, BundleRunner._s(run), timeTaken,
                               success, errors, BundleRunner._s(errors),
                               failures, BundleRunner._s(failures),
                               skipped
                            )
                )

    def run(self, bundeled_suites):
        overall_result  = None
        overall_time    = 0
        for bsuite in bundeled_suites:
            print('\n%s\n\tRunning test bundle "%s"\n%s\n\n' % (
                BundledTextTestResult.separator1,
                bsuite.get_name(),
                BundledTextTestResult.separator1
                ))
            result = None
            timeTaken = 0
            for suite in bsuite.get_suites():
                startTime = time.time()
                tmp_result = super(BundleRunner, self).run(suite)
                        #verbosity=0, 
                        ##stream=open(os.devnull, 'w'), 
                        #resultclass=BundledTextTestResult).run(suite)
                if result is None:
                    result = tmp_result
                else:
                    result.add_result(tmp_result)
                print('%s\n\n' % BundledTextTestResult.separator2)
                stopTime = time.time()
                timeTaken = timeTaken + stopTime - startTime

            self.print_result(result, timeTaken, 'Accumulated Bundle result:')

            if overall_result is None:
                overall_result = BundledTextTestResult(self.stream, 
                        self.descriptions,
                        self.verbosity, result)
            else:
                print("adding")
                overall_result.add_result(result)
            overall_time = overall_time + timeTaken

        self.stream.writeln()
        self.print_result(overall_result, overall_time, 'Accumulated Test result:')


