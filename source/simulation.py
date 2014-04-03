#!/usr/bin/env python
#
# $File: simulation.py $
# $LastChangedDate: 2014-01-14 10:38:56 -0600 (Tue, 14 Jan 2014) $
# $Rev: 2505 $
#
# This file is part of variant_tools, a software application to annotate,
# summarize, and filter variants for next-gen sequencing ananlysis.
# Please visit http://varianttools.sourceforge.net for details.
#
# Copyright (C) 2011 - 2014 Bo Peng (bpeng@mdanderson.org)
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

import sys, os, re
from .project import Project
from .utils import ProgressBar, DatabaseEngine, delayedAction, env
if sys.version_info.major == 2:
    from ucsctools_py2 import tabixFetch
else:
    from ucsctools_py3 import tabixFetch

import argparse

'''Draft design of the simulation feature

Goals:
1. Simulate 'real' data in the sense that the simulated datasets should have
  chromsome, locations, build, and preferrable realistic regions for 
  exome, etc.

2. Users provide description of samples, preferrably NOT the way to simulate
  it.

3. Results are written as variant tools projects, and should be easy to analyze
  using the subsequent tools. Results can be exported in vcf format.

4. Simulate SNPs, and Indels if model allows.

Design:
1. Use the existing 'show' feature to show available models.
  a. vtools show simulations/models/simu_models
  b. vtools show model SOME_MODEL

2. Use the existing 'snapshot' feature to distribute pre-simulated
  datasets.
  a. vtools show snapshots
  b. vtools admin --load_snapshot

3. Use the existing 'export' feature to export simulated data in vcf format
  a. vtools export --output simulated.vcf

4. Use the existing 'pipeline' feature to simulate complex samples if that
  evolves multiple steps.

Implementations:



Models:
1. Sequencing error model: manipulate existing (simulated) genotype
2. De Nova mutation model: create novel mutations for offspring
3. Phenotype model: create phenotype based on genotypes on selected
   variants.
4. Indel models.
5. Resampling model: easy to implement
6. Coalescane model: ... many stuff with python interface
7. forward-time model: simupop, srv

'''


class NullModel:
    '''A base class that defines a common interface for simulation models'''
    def __init__(self, *method_args):
        '''Args is arbitrary arguments, might need an additional parser to
        parse it'''
        # trait type
        self.trait_type = None
        # group name
        self.gname = None
        self.fields = []
        self.parseArgs(*method_args)
        #

    def parseArgs(self, method_args):
        # this function should never be called.
        raise SystemError('All association tests should define their own parseArgs function')


def getAllModels():
    '''List all simulation models (all classes that subclasses of NullModel) in this module'''
    return sorted([(name, obj) for name, obj in globals().iteritems() \
        if type(obj) == type(NullModel) and issubclass(obj, NullModel) \
            and name not in ('NullModel',)], key=lambda x: x[0])

def simulateArguments(parser):
    parser.add_argument('--regions', nargs='+',
        help='''One or more chromosome regions in the format of chr:start-end
        (e.g. chr21:33,031,597-33,041,570), or Field:Value from a region-based 
        annotation database (e.g. refGene.name2:TRIM2 or refGene_exon.name:NM_000947).
        Chromosome positions are 1-based and are inclusive at both ends so the 
        chromosome region has a length of end-start+1 bp. For the second case,
        multiple chromosomal regions will be selected if the  name matches more
        than one chromosomal regions.''')
    parser.add_argument('--model', 
        help='''Simulation model, which defines the algorithm and default
            parameter to simulate data. A list of model-specific parameters
            could be specified to change the behavior of these models. Commands
            vtools show models and vtools show model MODEL can be used to list
            all available models and details of one model.''')
    

def expandRegions(arg_region, arg_build, proj=None):
    if proj is None:
        proj = Project(verbosity=args.verbosity)
    regions = []
    for region in arg_region:
        try:
            chr, location = region.split(':', 1)
            start, end = location.split('-')
            start = int(start.replace(',', ''))
            end = int(end.replace(',', ''))
            if start == 0 or end == 0:
                raise ValueError('0 is not allowed as starting or ending position')
            if start > end:
                regions.append((chr, start, end, '(reverse complementary)'))
            else:
                regions.append((chr, start, end, ''))
        except Exception as e:
            # this is not a format for chr:start-end, try field:name
            try:
                field, value = region.split(':', 1)
                annoDB = None
                # now we need to figure out how to get start and end position...
                lines = getoutput(['vtools', 'show', 'fields'])
                for line in lines.split('\n'):
                    try:
                        field_name = line.split()[0]
                    except:
                        continue
                    if '.' not in field_name:
                        continue
                    if field == field_name or field == field_name.split('.')[-1]:
                        annoDB = field_name.split('.')[0]
                        field = field_name.split('.')[1]
                        break
                if annoDB is None:
                    raise ValueError('Cannot locate field {} in the current project'.format(field))
                # now we have annotation database
                # but we need to figure out how to use it
                anno_type = getoutput(['vtools', 'execute', 'SELECT value FROM {}.{}_info WHERE name="anno_type"'.format(annoDB, annoDB)])
                if anno_type.strip() != 'range':
                    raise ValueError('Only field from a range-based annotation database could be used.')
                # get the fields?
                build = eval(getoutput(['vtools', 'execute', 'SELECT value FROM {}.{}_info WHERE name="build"'.format(annoDB, annoDB)]))
                if arg_build in build:
                    chr_field, start_field, end_field = build[arg_build]
                else:
                    raise ValueError('Specified build {} does not match that of the annotation database.'.format(arg_build))
                #
                # find the regions
                output = getoutput(['vtools', 'execute', 'SELECT {},{},{} FROM {}.{} WHERE {}="{}"'.format(
                    chr_field, start_field, end_field, annoDB, annoDB, field, value)])
                for idx, line in enumerate(output.split('\n')):
                    try:
                        chr, start, end = line.split()
                        regions.append((chr, int(start), int(end), '({} {})'.format(region, idx+1)))
                    except:
                        pass
                if not regions:
                    env.logger.error('No valid chromosomal region is identified for {}'.format(region)) 
            except Exception as e:
                raise ValueError('Incorrect format for chromosomal region {}: {}'.format(region, e))
    return regions


def extractFromVCF(filenameOrUrl, regions, output=''):
    # This is equivalent to 
    #
    # tabix -h ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20100804/
    #     ALL.2of4intersection.20100804.genotypes.vcf.gz 2:39967768-39967768
    #
    #
    tabixFetch(filenameOrUrl, regions)

def simulate(args):
    try:
        with Project(verbosity=args.verbosity) as proj:
            # step 0: 
            # get the model of simulation
            #print expandRegions(args.regions, proj.build, proj)
            extractFromVCF(os.path.expanduser('~/vtools/test/vcf/CEU.vcf.gz'),
                ['1:1-100000'])

    except Exception as e:
        env.logger.error(e)
        sys.exit(1)


