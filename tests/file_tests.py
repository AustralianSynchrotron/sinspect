import os
import sys

PATH_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path = [os.path.join(PATH_HERE, '..')] + sys.path

import unittest
import nose
from nose.tools import eq_, ok_
from app import SpFile


TESTDATA_DIR = 'testdata'
#TESTDATA_DIR = os.path.join('tests', 'testdata')

''' The structure of test_data.xml is specifically built to test functionality of the
code. Changes to test_data.xml will cause failures in these tests.
'''

class DatasetLoadingTest(unittest.TestCase):
    def simple_load_test(self):
        filename = os.path.join(TESTDATA_DIR, 'test_data.xml')
        specs_file = SpFile().open(filename)
        ok_(isinstance(specs_file, SpFile))


class CorrectLoadingTest(unittest.TestCase):
    def setUp(self):
        filename = os.path.join(TESTDATA_DIR, 'test_data.xml')
        self.specs_file = SpFile().open(filename)

    def count_groups_test(self):
        eq_(len(self.specs_file.specs_groups), 2)

    def count_regions_test(self):
        regions = self.specs_file.specs_groups[0].specs_regions
        eq_(len(regions), 4)
        regions = self.specs_file.specs_groups[1].specs_regions
        eq_(len(regions), 1)

    def group_name_mangling_test(self):
        name1 = self.specs_file.specs_groups[0].name
        eq_(name1, 'Group1')
        name2 = self.specs_file.specs_groups[1].name
        eq_(name2, 'Group1-1')

    def region_name_mangling_test(self):
        name1 = self.specs_file.specs_groups[0].specs_regions[1].name
        eq_(name1, 'Carbon Nexafs Vanil_FI')
        name2 = self.specs_file.specs_groups[0].specs_regions[3].name
        eq_(name2, 'Carbon Nexafs Vanil_FI-1')
        name3 = self.specs_file.specs_groups[1].specs_regions[0].name
        eq_(name3, 'Carbon Nexafs Vanil_FI')


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
