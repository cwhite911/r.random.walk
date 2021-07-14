#!/usr/bin/env python

############################################################################
#
# NAME:      r_random_walk_test
#
# AUTHOR:    Corey T. White
#
# PURPOSE:   This is a test file for r.random.walk
#
# COPYRIGHT: (C) 2021 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

# Dependencies
from grass.gunittest.case import TestCase
from grass.gunittest.main import test

# Tests
class TestRandomWalk(TestCase):
    # Setup variables to be used for outputs
    random_walk = "test_random_walk"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        # cls.runModule or self.runModule is used for general module calls
        cls.runModule("g.region", raster="elevation")

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    @classmethod
    def tearDown(self):
        """
        Remove the outputs created from the centroids module
        This is executed after each test run.
        """
        self.runModule("g.remove", flags="f", type="raster", name=self.random_walk)

    def test_output(self):
        """Test that random.walk are expected output"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            "r.random.walk", input="elevation", output=self.random_walk, steps=1000, overwrite=True
        )

        # self.assert(
        #     self.random_walk, "data/random_walk_result", digits=6, precision=1
        # )


if __name__ == "__main__":
    test()
{"mode":"full","isActive":false}