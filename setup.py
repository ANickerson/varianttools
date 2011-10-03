#!/usr/bin/env python2.7
#
# $File: setup.py $
# $LastChangedDate: 2011-06-16 20:10:41 -0500 (Thu, 16 Jun 2011) $
# $Rev: 4234 $
#
# This file is part of variant_tools, a software application to annotate,
# summarize, and filter variants for next-gen sequencing ananlysis.
# Please visit http://variant_tools.sourceforge.net # for details.
#
# Copyright (C) 2011 Bo Peng (bpeng@mdanderson.org)
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

from distutils.core import setup, Extension
try:
   from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
   from distutils.command.build_py import build_py

import sys

#
VTOOLS_VERSION = '1.0beta'
#
# the association module is not ready for prime time...
# 
with_association = False

if with_association:
   
   # Under linux/gcc, lib stdc++ is needed for C++ based extension.
   if sys.platform == 'linux2':
      libs = ['stdc++']
   else:
      libs = []
      
   asso_module = [
        'variant_tools.association',
        'variant_tools.assoTests'    # will be generated by SWIG
      ]
   ext_module = [
        Extension('variant_tools/_assoTests',
            sources = ['variant_tools/assoTests.i',
                'variant_tools/assoData.cpp'],
            swig_opts = ['-O', '-shadow', '-c++', '-keyword',],
            library_dirs = [],
            libraries = libs,
            include_dirs = ["."],
        )
      ]
else:
    asso_module = []
    ext_module = []

setup(name = "variant_tools",
    version = VTOOLS_VERSION,
    description = "Variant tools: an integrated annotation and analysis package for next-gen sequencing data",
    author = 'Bo Peng',
    url = 'http://varianttools.sourceforge.net',
    author_email = 'bpeng@mdanderson.org',
    maintainer = 'Bo Peng',
    maintainer_email = 'varianttools-devel@lists.sourceforge.net',
    py_modules = [
        'variant_tools.__init__',
        'variant_tools.utils',
        'variant_tools.project',
        'variant_tools.importer',
        'variant_tools.exporter',
        'variant_tools.sample',
        'variant_tools.variant',
        'variant_tools.annotation',
        'variant_tools.liftOver',
    ] + asso_module,
    scripts = [
        'vtools',
        'vtools_report'
    ],
    cmdclass = {'build_py': build_py },
    package_dir = {'variant_tools': 'variant_tools'},
    ext_modules = ext_module
)

