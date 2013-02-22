import unittest
import nose
from nose import SkipTest
from nose.tools import eq_, ok_
import os
import numpy as np
from app import SpecsFile, TreePanel


TESTDATA_DIR = 'testdata'
#TESTDATA_DIR = os.path.join('tests', 'testdata')

''' The structure of test_data.xml is specifically built to test functionality of the
code. Changes to test_data.xml will cause failures in these tests.
'''

class AxisTypeTest(unittest.TestCase):
    def setUp(self):
        filename = os.path.join(TESTDATA_DIR, 'test_data.xml')
        self.specs_file = SpecsFile().open(filename)

    def get_x_axis_test(self):
        region = self.specs_file.specs_groups[0].specs_regions[0].region
        eq_(region.scan_mode, 'ConstantFinalState')


class SingleNormalisationTest(unittest.TestCase):
    def setUp(self):
        filename = os.path.join(TESTDATA_DIR, 'test_data.xml')
        self.tree_panel = TreePanel(specs_file=SpecsFile())
        self.specs_file = SpecsFile().open(filename)

    def single_normalisation_test(self):
        raise SkipTest
        self.tree_panel.extended_channel_ref = 3     #'Nexafs_double_reference_Photodiode_in_chamber'
        region = self.specs_file.specs_groups[0].specs_regions[0]
        extended_ch5 = self.specs_file.specs_groups[0].specs_regions[1].region.extended_channels[:,5-1]
        ys = extended_ch5
        region.normalise_self(ys)
        ok_(np.allclose( [extended_ch5[0], extended_ch5[-1]],
                         [1.9564414,       0.83147091      ] ))


class DoubleNormalisationTest(unittest.TestCase):
    def setUp(self):
        filename = os.path.join(TESTDATA_DIR, 'test_data.xml')
        self.specs_file = SpecsFile().open(filename)

    def double_normalisation_test(self):
        raise SkipTest
        ok_(False)


if __name__ == '__main__':
    nose.main()
