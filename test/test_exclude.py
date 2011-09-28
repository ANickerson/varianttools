#!/usr/bin/env python
#
# $File: test_exclude.py $
# $LastChangedDate: 2011-06-16 20:10:41 -0500 (Thu, 16 Jun 2011) $
# $Rev: 4234 $
#
# This file is part of variant_tools, a software application to annotate,
# summarize, and filter variants for next-gen sequencing ananlysis.
# Please visit http://variant_tools.sourceforge.net # for details.
#
# Copyright (C) 2004 - 2010 Bo Peng (bpeng@mdanderson.org)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os
import glob
import unittest
import subprocess
from testUtils import ProcessTestCase, runCmd, initTest

class TestExclude(ProcessTestCase):
    def setUp(self):
        'Create a project'
        initTest(12)
    def removeProj(self):
        runCmd('vtools remove project')
    def testExclude(self):
        'Test command vtools exclude'
        self.assertFail('vtools exclude')
        self.assertSucc('vtools exclude -h')
        # Variant table non_existing_table does not exist.
        self.assertFail('vtools exclude non_existing_table "aff=\'1\'" -t aff')
        # Cannot overwrite master variant table. Please choose another name for the variant table.
        self.assertFail('vtools exclude ns "sift_score<=0.95" -t variant')
        self.assertSucc('vtools exclude ns "sift_score <= 0.95" -t ns_non_damaging')
        self.assertSucc('vtools exclude input_tsv "variant_id<708" -t id708')
        self.assertSucc('vtools exclude ns "sift_score <= 0.95" -c')

if __name__ == '__main__':
    unittest.main()
