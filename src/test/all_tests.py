import glob
import unittest
import sys

sys.path.append('../code/machine_learning_model')

def create_test_suite():
    test_file_strings = glob.glob('test/test_*.py')
    module_strings = ['test.'+str[5:len(str)-3] for str in test_file_strings]
    suites = [unittest.defaultTestLoader.loadTestsFromName(name) \
              for name in module_strings]
    testSuite = unittest.TestSuite(suites)
    return testSuite