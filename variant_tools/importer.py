#!/usr/bin/env python
#
# $File: importer.py $
# $LastChangedDate$
# $Rev$
#
# This file is part of variant_tools, a software application to annotate,
# summarize, and filter variants for next-gen sequencing ananlysis.
# Please visit http://varianttools.sourceforge.net for details.
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

import os
import sys
import gzip
import bz2
import re
import array
import threading
import Queue
from heapq import heappush, heappop, heappushpop
from cPickle import dumps, loads, HIGHEST_PROTOCOL
from binascii import a2b_base64, b2a_base64
from subprocess import Popen, PIPE
from multiprocessing import Process, Pipe
from itertools import izip, repeat
from collections import defaultdict
from .project import Project, fileFMT
from .liftOver import LiftOverTool
from .utils import ProgressBar, lineCount, getMaxUcscBin, delayedAction, \
    normalizeVariant, openFile, DatabaseEngine, hasCommand, consolidateFieldName, \
    downloadFile

#
#
# Functors to process input 
#
#
# Extractors to extract value from a field
class ExtractField:
    def __init__(self, index, sep=';', default=None):
        '''Define an extractor that returns the index-th (1-based) field of the fields
        separated by specified delimiter. Return default if unsuccessful.'''
        self.index = index - 1
        self.sep = sep
        self.default = default
    
    def __call__(self, item):
        try:
            return item.split(self.sep, self.index + 1)[self.index]
        except:
            return self.default

class CheckSplit:
    def __init__(self, sep=','):
        '''Define an extractor that returns all items in a field separated by
        specified delimiter. Return default if unsuccessful. It differs from
        SplitField in that it will return the item itself (instead of a tuple
        of one element) when there is only one element. The item will then
        will copy if multiple items exist.'''
        self.sep = sep
    
    def __call__(self, item):
        return item if self.sep not in item else tuple(item.split(self.sep))
    
class SplitField:
    def __init__(self, sep=','):
        '''Define an extractor that returns all items in a field separated by
        specified delimiter. These items will lead to multiple records in
        the database.'''
        self.sep = sep
    
    def __call__(self, item):
        return tuple(item.split(self.sep))

class ExtractFlag:
    def __init__(self, name, sep=';'):
        '''Define an extractor that returns 1 is item contains name as one of the fields,
        and 0 otherwise. No space is allowed between delimiter and flag.'''
        self.n = name
        self.s = name + sep
        self.e = sep + name
        self.m = sep + name + sep
    
    def __call__(self, item):
        # this should be faster than
        #
        #     if self.name in item.split(self.sep):
        # 
        # because we do not have to split the whole string.
        #
        if self.n not in item:
            return '0'
        # put the most common case first
        if self.m in item or item.startswith(self.s) or item.endswith(self.e) or item == self.n:
            return '1'
        else:
            return '0'

class CommonLeading:
    def __init__(self):
        pass

    def _commonLeading(self, ref, alt):
        common_leading = 0
        for i in range(min(len(ref), len(alt))):
            if ref[i] == alt[i]:
                common_leading += 1
        return ref[:common_leading]

    def __call__(self, item):
        if ',' in item[1]:
            return tuple([self._commonLeading(item[0], alt) for alt in item[1].split(',')])
        else:
            return self._commonLeading(item[0], item[1])

class CommonEnding:
    def __init__(self):
        pass
    
    def _commonEnding(self, ref, alt):
        common_leading = 0
        for i in range(min(len(ref), len(alt))):
            if ref[i] == alt[i]:
                common_leading += 1
        if common_leading > 0:
            ref = ref[common_leading:]
            alt = alt[common_leading:]
        common_ending = 0
        for i in range(-1, - min(len(ref), len(alt)) - 1, -1):
            if ref[i] == alt[i]:
                common_ending -= 1
            else:
                break
        if common_ending < 0:
            return ref[common_ending:]
        else:
            return ''
    
    def __call__(self, item):
        if ',' in item[1]:
            return tuple([self._commonEnding(item[0], alt) for alt in item[1].split(',')])
        else:
            return self._commonEnding(item[0], item[1])


class __FieldFromFormat:
    def __init__(self, name, sep=';', default=None):
        '''Define an extractor that return the value of a field according 
        to a format string. This is used to extract stuff from the format
        string of vcf files.
        '''
        self.name = name
        self.sep = sep
        self.default = default
        self.factory = defaultdict(dict)
        self.index = {}

    def __call__(self, item):
        try:
            # first try to get from a global factory
            return self.factory[item[0]][item[1]]
        except:
            fmt, val = item
            try:
                # now split .... assuming the format has been handled before.
                # this should be the case most of the time
                res = val.split(self.sep)[self.index[fmt]]
                # we assume that the most common ones has been added...
                # and we do not want to add all sorts of rare values forever
                if len(self.factory[fmt]) < 10000:
                    self.factory[fmt][val] = res
                return res
            except:
                # if the format has not been handled before.
                if fmt not in self.index:
                    fields = fmt.split(self.sep)
                    if self.name in fields:
                        self.index[fmt] = fields.index(self.name)
                    else:
                        self.index[fmt] = None
                # try again
                try:
                    res = val.split(self.sep)[self.index[fmt]]
                    if len(self.factory[fmt]) < 10000:
                        self.factory[fmt][val] = res
                    return res
                # if still error
                except:
                    self.factory[fmt][val] = self.default
                    return self.default

__all_field_from_format = {}

def FieldFromFormat(name, sep=';', default=None):
    # this is a factory of __FieldFromFormat class
    #
    global __all_field_from_format
    if (name, sep, default) in __all_field_from_format:
        return __all_field_from_format[(name, sep, default)]
    else:
        obj = __FieldFromFormat(name, sep, default)
        __all_field_from_format[(name, sep, default)] = obj
        return obj

class VcfGenotype:
    def __init__(self, default=None):
        '''Define an extractor that extract genotype from a .vcf file'''
        self.default = default
        self.map = {'0/0': default, '0|0': default,
            '0/1': ('1',), '1/0': ('1',), '0|1': ('1',), '1|0': ('1',),
            '1/1': ('2',), '1|1': ('2',),
            '0/2': ('0', '1'), '2/0': ('0', '1'), '0|2': ('0', '1'), '2|0': ('0', '1'), 
            '1/2': ('-1', '-1'), '2/1': ('-1', '-1'), '1|2': ('-1', '-1'), '2|1': ('-1', '-1'),
            '2/2': ('0', '2'), '2|2': ('0', '2'),
            '0': default, '1': ('1',)}

    def __call__(self, item):
        # the most common and correct case...
        try:
            return self.map[item.partition(':')[0]]
        except KeyError:
            return None

class VcfGenoFromFormat:
    def __init__(self, default=None):
        '''Define an extractor that return genotype according to a format string.
        This is used to extract genotype from the format string of vcf files.
        '''
        self.fmt = '\t'
        self.idx = None
        self.default = default
        self.map = {'0/0': default, '0|0': default,
            '0/1': ('1',), '1/0': ('1',), '0|1': ('1',), '1|0': ('1',),
            '1/1': ('2',), '1|1': ('2',),
            '0/2': ('0', '1'), '2/0': ('0', '1'), '0|2': ('0', '1'), '2|0': ('0', '1'), 
            '1/2': ('-1', '-1'), '2/1': ('-1', '-1'), '1|2': ('-1', '-1'), '2|1': ('-1', '-1'),
            '2/2': ('0', '2'), '2|2': ('0', '2'),
            '0': default, '1': ('1',)}

    def __call__(self, item):
        # the most common and correct case...
        try:
            if item[0][:2] == 'GT':
                return self.map[item[1].partition(':')[0]]
            elif item[0] != self.fmt:
                fmt, val = item
                self.fmt = fmt
                fields = fmt.split(':')
                if 'GT' in fields:
                    self.idx = fields.index('GT')
                    return self.map[val.split(':')[self.idx]]
                else:
                    self.idx = None
                    return self.default
            return self.map[item[1].split(':', self.idx + 1)[self.idx]] if self.idx is not None else self.default
        except KeyError:
            return None
        
class ExtractValue:
    def __init__(self, name, sep=';', default=None):
        '''Define an extractor that returns the value after name in one of the fields,
        and a default value if no such field is found. No space is allowed between 
        delimiter and the name.'''
        self.name = name
        self.sep = sep
        #self.pos = len(name)
        self.default = default

    def __call__(self, item):
        if self.name not in item:
            return self.default
        #
        # Using two partisions seems to be a tiny bit faster than 
        # split and startswith
        #
        #for field in item.split(self.sep):
        #    if field.startswith(self.name):
        #        return field[self.pos:]
        ss = item.partition(self.name)
        return ss[2].partition(self.sep)[0] if ss[2] is not None else self.default

class IncreaseBy:
    def __init__(self, inc=1):
        '''Adjust position'''
        self.inc = inc

    def __call__(self, item):
        return str(int(item) + self.inc) if item.isdigit() else None

class MapValue:
    '''Map value to another one, return default if unmapped'''
    def __init__(self, map, default=None):
        self.map = map
        self.default = default

    def __call__(self, item):
        try:
            return self.map[item]
        except:
            return self.default
        
class RemoveLeading:
    def __init__(self, val):
        self.val = val
        self.vlen = len(val)

    def __call__(self, item):
        return item[self.vlen:] if item.startswith(self.val) else item

class EncodeGenotype:
    '''Encode 1/1, 1/2 etc to variant tools code'''
    def __init__(self, default=None):
        self.map = {'0/0': default, '0|0': default,
            '0/1': ('1',), '1/0': ('1',), '0|1': ('1',), '1|0': ('1',),
            '1/1': ('2',), '1|1': ('2',),
            '0/2': ('0', '1'), '2/0': ('0', '1'), '0|2': ('0', '1'), '2|0': ('0', '1'), 
            '1/2': ('-1', '-1'), '2/1': ('-1', '-1'), '1|2': ('-1', '-1'), '2|1': ('-1', '-1'),
            '2/2': ('0', '2'), '2|2': ('0', '2'),
            '0': default, '1': ('1',)}

    def __call__(self, item):
        return self.map[item]
        
class Nullify:
    def __init__(self, val):
        self.val = val
        if type(self.val) == str:
            self.__call__ = self.nullify_single
        else:
            self.__call__ = self.nullify_multiple

    def nullify_single(self, item):
        return None if item == self.val else item

    def nullify_multiple(self, item):
        return None if item in self.val else item

class IgnoredRecord(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)

class DiscardRecord:
    def __init__(self, val):
        self.val = val
        if type(self.val) == str:
            self.__call__ = self.discard_single
        else:
            self.__call__ = self.discard_multiple

    def discard_single(self, item):
        if item == self.val:
            raise IgnoredRecord()
        return item

    def discard_multiple(self, item):
        if item in self.val:
            raise IgnoredRecord()
        return item
    
__databases = {}

class _DatabaseQuerier:
    '''This query a field from an annotation database'''
    def __init__(self, cursor, name, res_field, cond_fields, default=None):
        '''Supose res_field is alt, cond_fields are chr,pos, this querier
        will get alt using query
          SELECT dbSNP.alt FROM dbSNP WHERE chr=VAL1 AND pos=VAL2
        '''
        self.default = default
        self.cur = cursor
        self.query = 'SELECT {} FROM {} WHERE {}'.format(res_field,
            name, ' AND '.join(['{}=?'.format(x) for x in cond_fields]))

    def __call__(self, item):
        self.cur.execute(self.query, item)
        res = self.cur.fetchall()
        if len(res) == 1:
            return res[0][0]
        elif len(res) > 1:
            return tuple([x[0] for x in res])
        else:
            return self.default

def DatabaseQuerier(dbfile, res_field, cond_fields, default=None):
    global __databases
    if dbfile not in __databases:
        db = DatabaseEngine()
        if not os.path.isfile(dbfile):
            raise ValueError('Database file {} does not exist'.format(dbfile))
        db.connect(dbfile)
        cur = db.cursor()
        tables = db.tables()
        try:
            name = [x for x in tables if x.endswith('_info')][0][:-5]
        except Exception as e:
            raise ValueError('Incorrect database (missing info table): {}'.format(e))
        if not name in tables:
            raise ValueError('Incorrect database (missing table {})'.format(name))
        if not name + '_field':
            raise ValueError('Incorrect database (missing field table)')
        for fld in cond_fields.split(','):
            if not db.hasIndex('{}_idx'.format(fld)):
                cur.execute('CREATE INDEX {0}_idx ON {1} ({0} ASC);'.format(fld, name))
        __databases[dbfile] = (cur, name)
    return _DatabaseQuerier(__databases[dbfile][0], __databases[dbfile][1], 
        res_field, cond_fields.split(','), default)

class SequenceExtractor:
    '''This sequence extractor extract subsequence from a pre-specified sequence'''
    def __init__(self, filename):
        if not os.path.isfile(filename):
            filename = downloadFile(filename)
        if not os.path.isfile(filename):
            raise valueError('Failed to obtain sequence file {}'.format(filename))
        # a dictionary for seq for each chromosome
        self.seq = {}
        # we assume that the input file has format
        #
        # >chr9
        # seq
        # >chr10
        # seq
        #
        current_chr = None
        # openFile can open .gz file directly
        cnt = lineCount(filename)
        prog = ProgressBar('Reading ref genome sequences', cnt)
        with openFile(filename) as input:   
            # for each chromosome? need to fix it here
            for idx, line in enumerate(input):
                line = line.decode()
                if line.startswith('>'):
                    chr = line[1:].split()[0]
                    if chr.startswith('chr'):
                        chr = chr[3:] 
                    self.seq[chr] = array.array('b', [])
                else:
                    self.seq[chr].fromstring(line.rstrip())
                if idx % 10000 == 0:
                    prog.update(idx)
        # use another key with 'chr' to point to the same item so that the dictionary 
        # works with both ['2'] and ['chr2']
        for key in self.seq:
            self.seq['chr' + key] = self.seq[key]
        prog.done()

    def __call__(self, item):
        return self.seq[item[0]][item[1]]

# this is a dictionary to save extractors for each file used
g_SeqExtractor = {}
def SeqAtLoc(filename):
    # return the same object for multiple instances of SeqAtLoc because
    # we do not want to read the fasta file multiple times
    if filename not in g_SeqExtractor:
        g_SeqExtractor[filename] = SequenceExtractor(filename)
    return g_SeqExtractor[filename]
    
class SequentialExtractor:
    def __init__(self, extractors):
        '''Define an extractor that calls a list of extractors. The string extracted from
        the first extractor will be passed to the second, and so on.'''
        self.extractors = []
        for e in extractors:
            if hasattr(e, '__call__'):
                self.extractors.append(e.__call__)
            else:
                self.extractors.append(e)

    def __call__(self, item):
        for e in self.extractors:
            # if multiple records are returned, apply to each of them
            if type(item) is tuple:
                if type(item[0]) is tuple:
                    raise ValueError('Nested vector extracted is not allowed')
                item = tuple(e(x) for x in item)
            # if item is None or ''
            elif not item:
                return item
            else:
                item = e(item)
        return item

#
#
# Process each line using the above functors
#
class LineImporter:
    '''An intepreter that read a record, process it and return processed records.'''
    def __init__(self, fields, build, delimiter, merge_by_cols, logger):
        '''Fields: a list of fields with index, adj (other items are not used)
        builds: index(es) of position, reference allele and alternative alleles. If 
            positions are available, UCSC bins are prepended to the records. If reference
            and alternative alleles are available, the records are processed for correct
            format of ref and alt alleles.
        '''
        self.logger = logger
        self.build = build
        self.raw_fields = fields
        self.fields = []
        self.delimiter = delimiter
        self.merge_by_cols = merge_by_cols
        self.columnRange = [None] * len(self.raw_fields)
        self.first_time = True
        self.valid_till = None  # genotype fields might be disabled
        # used to report result
        self.processed_lines = 0
        self.skipped_lines = 0
        self.num_records = 0

    def reset(self, validTill=None):
        self.first_time = True
        self.fields = []
        self.nColumns = 0
        self.valid_till = validTill

    def process(self, tokens):
        if type(tokens) is not list:
            tokens = [x.strip() for x in tokens.split(self.delimiter)]
        if self.first_time:
            self.nColumns = len(tokens)
            cIdx = 0
            for fIdx, field in enumerate(self.raw_fields):
                if self.valid_till is not None and fIdx >= self.valid_till:
                    continue
                try:
                    # get an instance of an extractor, or a function
                    e = eval(field.adj) if field.adj else None
                    # 1. Not all passed object has __call__ (user can define a lambda function)
                    # 2. Althoug obj(arg) is equivalent to obj.__call__(arg), saving obj.__call__ to 
                    #    e will improve performance because __call__ does not have to be looked up each time.
                    # 3. Passing object directly has an unexpected side effect on performance because comparing
                    #    obj to 1 and 'c' later are very slow because python will look for __cmp__ of the object.
                    if hasattr(e, '__iter__'):
                        # if there are multiple functors, use a sequential extractor to handle them
                        e = SequentialExtractor(e)
                    if hasattr(e, '__call__'):
                        e = e.__call__
                    indexes = []
                    for x in field.index.split(','):
                        if ':' in x:
                            # a slice
                            if x.count(':') == 1:
                                start,end = map(str.strip, x.split(':'))
                                step = None
                            else:
                                start,end,step = map(str.strip, x.split(':'))
                                step = int(step) if step else None
                            start = int(start) - 1 if start else None
                            if end.strip():
                                if int(end) >= 0:   # position index, shift by 1
                                    end = int(end) - 1
                                else:               # relative to the back, do not move
                                    end = int(end)
                            else:
                                end = None
                            indexes.append(slice(start, end, step))
                        else:
                            # easy, an integer
                            indexes.append(int(x) - 1)
                    #
                    if ':' not in field.index:
                        if len(indexes) == 1:
                            # int, True means 'not a tuple'
                            self.fields.append((indexes[0], True, e))
                            self.columnRange[fIdx] = (cIdx, cIdx+1)
                            cIdx += 1
                        else:
                            # a tuple
                            self.fields.append((tuple(indexes), False, e))
                            self.columnRange[fIdx] = (cIdx, cIdx+1)
                            cIdx += 1
                    elif len(indexes) == 1:
                        # single slice
                        cols = range(len(tokens))[indexes[0]]
                        for c in cols:
                            self.fields.append((c, True, e))
                        self.columnRange[fIdx] = (cIdx, cIdx + len(cols))
                        cIdx += len(cols)
                    else:
                        # we need to worry about mixing integer and slice
                        indexes = [repeat(s, len(tokens)) if type(s) == int else range(len(tokens))[s] for s in indexes]
                        count = 0
                        for c in izip(*indexes):
                            count += 1
                            self.fields.append((tuple(c), False, e))
                        self.columnRange[fIdx] = (cIdx, cIdx + count)
                        cIdx += count
                except Exception as e:
                    sys.exit('Incorrect value adjustment functor or function {}: {}'.format(field.adj, e))
                    raise ValueError('Incorrect value adjustment functor or function {}: {}'.format(field.adj, e))
            self.first_time = False
        #
        try:
            # we first trust that nothing can go wrong and use a quicker method
            records = [(tokens[col] if t else [tokens[x] for x in col]) if adj is None else \
                (adj(tokens[col]) if t else adj([tokens[x] for x in col])) for col,t,adj in self.fields]
        except IgnoredRecord as e:
            return
        except Exception:
            # If anything wrong happends, process one by one to get a more proper error message (and None values)
            records = []
            for col, t, adj in self.fields:
                try:
                    item = tokens[col] if t else [tokens[x] for x in col]
                except IndexError:
                    raise ValueError('Cannot get column {} of the input line, which has only {} columns (others have {} columns).'.format(\
                        col + 1 if type(col) is int else [x+1 for x in col], len(tokens), self.nColumns))
                if adj is not None:
                    try:
                        item = adj(item)
                    except Exception as e:
                        self.logger.debug('Failed to process field {}: {}'.format(item, e))
                        # missing ....
                        item = None
                records.append(item)
        #
        num_records = max([len(item) if type(item) is tuple else 1 for item in records]) if records else 1
        # handle records
        if not self.build:
            # there is no build information, this is 'field' annotation, nothing to worry about
            if num_records == 1:
                yield [], [x[0] if type(x) is tuple else x for x in records]
            else:
                for i in range(num_records):
                    yield [], [(x[i] if i < len(x) else None) if type(x) is tuple else x for x in records]
        elif len(self.build[0]) == 1:
            for i in range(num_records):
                if i == 0:  # try to optimize a little bit because most of the time we only have one record
                    rec = [x[0] if type(x) is tuple else x for x in records]
                else:
                    rec = [(x[i] if i < len(x) else None) if type(x) is tuple else x for x in records]
                bins = [getMaxUcscBin(int(rec[pos_idx]) - 1, int(rec[pos_idx])) if rec[pos_idx] else None for pos_idx, in self.build]
                yield bins, rec
        else:
            for i in range(num_records):
                bins = []
                if i == 0:  # try to optimize a little bit because most of the time we only have one record
                    rec = [x[0] if type(x) is tuple else x for x in records]
                else:
                    rec = [(x[i] if i < len(x) else None) if type(x) is tuple else x for x in records]
                for pos_idx, ref_idx, alt_idx in self.build:
                    bin, pos, ref, alt = normalizeVariant(int(rec[pos_idx]) if rec[pos_idx] else None, rec[ref_idx], rec[alt_idx])
                    bins.append(bin)
                    rec[pos_idx] = pos
                    rec[ref_idx] = ref
                    rec[alt_idx] = alt
                yield bins, rec


#
#
# Write genotype to disk
# 
#

def GenotypeWriter(proj, geno, geno_info, sample_ids):
    if len(sample_ids) == 1 or not hasCommand(['sort', '-h']):
        return DirectGenotypeWriter(proj, geno, geno_info, sample_ids)
    else:
        return SortGenotypeWriter(proj, geno, geno_info, sample_ids)

class DirectGenotypeWriter:
    def __init__(self, proj, geno, geno_info, sample_ids):
        self.proj = proj
        self.logger = proj.logger
        self.logger.debug('Using a direct genotype writer')
        self.geno_db = '{}_genotype'.format(proj.name)
        #
        self.db = DatabaseEngine()
        self.db.connect(self.geno_db)
        self.query = 'INSERT INTO genotype_{{}} VALUES ({0});'\
            .format(','.join([self.db.PH] * (1 + len(geno) + len(geno_info))))
        self.cur = self.db.cursor()
        s = delayedAction(self.logger.info, 'Creating {} genotype tables'.format(len(sample_ids)))
        for idx, sid in enumerate(sample_ids):
            # create table
            self.proj.createNewSampleVariantTable(self.cur,
                'genotype_{0}'.format(sid), len(geno) > 0, geno_info)
        self.db.commit()
        del s
        self.count = 0

    def write(self, id, rec):
        self.cur.execute(self.query.format(id), rec)
        self.count += 1
        if self.count % 500000 == 0:
            self.db.commit()
    
    def close(self):
        self.db.commit()
        self.db.close()

class SortGenotypeWriter:
    '''This genotype writer sort samples before they are inserted to 
        the genotype database. This greatly helps the performance of subsequent
        operations on the genotype table because tables are not scattered
        around the whole database.
    '''
    def __init__(self, proj, geno, geno_info, sample_ids):
        self.proj = proj
        self.logger = proj.logger
        self.geno = geno
        self.geno_info = geno_info
        self.sample_ids = sample_ids
        #
        self.batch_count = 0
        self.file_idx = 0
        #
        sorted_file = open(os.path.join('cache', 'temp_db_{}.sorted'.format(self.file_idx)), 'w')
        self.sorted_files = [sorted_file]
        #
        psort = Popen(['sort', '-k1', '-n', '-s', '--temporary-directory=cache'], stdin=PIPE, stdout=sorted_file)
        self.psort = [psort]
        #
        self.output = psort.stdin
        #
        RAM_CACHE_SIZE = 10000000   # we cache 10M records
        RAM_CACHE_RECORDS = RAM_CACHE_SIZE // (1 + len(geno) + len(geno_info)) // len(sample_ids) # number of records
        RECORDS_PER_BATCH = max(RAM_CACHE_RECORDS, 100)    # at least 100 in batch
        self.RECORDS_PER_BATCH = min(RECORDS_PER_BATCH, 5000)   # at most 5000 in batch
        DISK_CACHE_SIZE = 1000000000  # 1G records per temp file
        DISK_CACHE_BATCHES = DISK_CACHE_SIZE // (self.RECORDS_PER_BATCH * (1 + len(geno) + len(geno_info)))
        self.DISK_CACHE_BATCHES = max(DISK_CACHE_BATCHES, 1000)  # at least 1000 batches per temp file
        #
        # for testing
        #self.RECORDS_PER_BATCH=20
        #self.DISK_CACHE_BATCHES=2000
        self.logger.debug('Using a sorted genotype writer with {} per sort entry and {} per temp file'.format(self.RECORDS_PER_BATCH, self.DISK_CACHE_BATCHES))
        #
        self.cache = {x: [] for x in sample_ids}

    def write(self, id, rec):
        if len(self.cache[id]) < self.RECORDS_PER_BATCH:
            self.cache[id].append(rec)
        else:
            # encode the entire list ....
            self.output.write('{}\t'.format(id).encode())
            self.output.write(b2a_base64(dumps(self.cache[id], HIGHEST_PROTOCOL)))
            self.cache[id] = []
            self.batch_count += 1
            if self.batch_count == self.DISK_CACHE_BATCHES:
                # close the previous one
                self.output.close()
                # check if existing processes have been finished
                # we will need to close some files in case too many temporary files are used
                for idx, (p, f) in enumerate(zip(self.psort, self.sorted_files)):
                    if p.poll() is not None:   # if it is done
                        f.close()              # close file
                        self.psort[idx] = None
                        self.sorted_files[idx] = None
                self.psort = [x for x in self.psort if x is not None]
                self.sorted_files = [x for x in self.sorted_files if x is not None]
                #
                # a new disk file
                self.file_idx += 1
                sorted_file = open(os.path.join('cache', 'temp_db_{}.sorted'.format(self.file_idx)), 'w')
                self.sorted_files.append(sorted_file)
                # a new process
                psort = Popen(['sort', '-k1', '-n', '-s', '--temporary-directory=cache'], stdin=PIPE, stdout=sorted_file)
                self.psort.append(psort)
                # reset batch count
                self.batch_count = 0
                # direct to a new output
                self.output = psort.stdin
    
    def close(self):
        # tell sort everything is done so we can start reading
        for id in self.sample_ids:
            if len(self.cache[id]) > 0:
                self.output.write('{}\t'.format(id).encode())
                self.output.write(b2a_base64(dumps(self.cache[id], HIGHEST_PROTOCOL)))
        del self.cache
        self.output.close()
        # 
        # wait for everyone to finish
        s = delayedAction(self.logger.info, 'Preparing genotypes for copying')
        # if there are more than one files, do a merge sort
        for p in self.psort:
            p.wait()
        # close all files
        for f in self.sorted_files:
            f.close()
        del s
        #
        db = DatabaseEngine()
        db.connect('{}_genotype'.format(self.proj.name))
        cur = db.cursor()
        query = 'INSERT INTO genotype_{{}} VALUES ({0});'\
            .format(','.join([db.PH] * (1 + len(self.geno) + len(self.geno_info))))
        prog = ProgressBar('Copying samples', len(self.sample_ids))
        last_id = None
        if self.file_idx == 0:
            source = open(os.path.join('cache', 'temp_db_0.sorted'), 'rb')
        else:
            psort = Popen(['sort', '-k1', '-n', '-s', '-m'] + \
                [os.path.join('cache', 'temp_db_{}.sorted'.format(x)) for x in range(self.file_idx + 1)],
                stdin=None, stdout=PIPE)
            source = psort.stdout
        sample_count = 0
        remaining_ids = set(self.sample_ids)
        for input in source:
            # we could use split('\t', 1) but python3 requires split(b'\t', 1) which does not exist in python2
            # rstrip is not needed because a2b_base64 can handle it
            id, items = input.split(None, 1)
            id = int(id)
            if id != last_id:
                last_id = id
                remaining_ids.remove(id)
                # a new table 
                db.commit()
                self.proj.createNewSampleVariantTable(cur, 'genotype_{0}'.format(id),
                    len(self.geno) > 0, self.geno_info)
                sample_count += 1
                prog.update(sample_count)
            # execute many is supposed to be faster than execute...
            cur.executemany(query.format(id), loads(a2b_base64(items)))
        source.close()
        prog.done()
        # Write empty genotype tables in the genotype database
        for id in remaining_ids:
            self.proj.createNewSampleVariantTable(cur, 'genotype_{0}'.format(id),
                len(self.geno) > 0, self.geno_info)
        # remove all temp files
        try:
            for x in range(self.file_idx + 1):
                os.remove(os.path.join('cache', 'temp_db_{}.sorted'.format(x)))
        except:
            pass
        #self.logger.info('{} genotypes in {} samples are copied'.format(genotype_count, sample_count))
        db.commit()
        db.close()


# Read record from disk file
#
class TextWorker(Process):
    #
    # This class starts a process and use passed LineProcessor
    # to process input line. If multiple works are started,
    # they read lines while skipping lines (e.g. 1, 3, 5, 7, ...)
    #
    def __init__(self, processor, input, varIdx, output, step, index, encoding, logger):
        self.processor = processor
        self.input = input
        self.output = output
        self.step = step
        self.varIdx = varIdx
        self.index = index
        self.encoding = encoding
        self.logger = logger
        Process.__init__(self)

    def run(self): 
        first = True
        num_records = 0
        skipped_lines = 0
        line_no = 0
        with openFile(self.input) as input_file:
            for line in input_file:
                line_no += 1
                if line_no % self.step != self.index:
                    continue
                line = line.decode(self.encoding)
                try:
                    if line.startswith('#'):
                        continue
                    for bins,rec in self.processor.process(line):
                        if first:
                            self.output.send(self.processor.columnRange)
                            first = False
                        num_records += 1
                        if self.varIdx is not None:
                            var_key = (rec[0], rec[2], rec[3])
                            if (var_key not in self.varIdx) or (rec[1] not in self.varIdx[var_key]):
                                continue
                        self.output.send((line_no, bins, rec))
                except Exception as e:
                    self.logger.debug('Failed to process line "{}...": {}'.format(line[:20].strip(), e))
                    skipped_lines += 1
        # if still first (this thread has not read anything), still send the columnRange stuff
        if first:
            self.output.send(self.processor.columnRange)
        # everything is done, stop the pipe
        self.output.send(None)
        # and send the summary statistics
        self.output.send((num_records, skipped_lines))
        self.output.close()

def TextReader(processor, input, varIdx, jobs, encoding, logger):
    if jobs == 0:
        return EmbeddedTextReader(processor, input, varIdx, encoding, logger)
    elif jobs == 1:
        return StandaloneTextReader(processor, input, varIdx, encoding, logger)
    else:
        return MultiTextReader(processor, input, varIdx, jobs, encoding, logger)

class EmbeddedTextReader:
    #
    # This processor uses the passed line processor to process input
    # in the main process. No separate process is spawned.
    #
    def __init__(self, processor, input, varIdx, encoding, logger):
        self.num_records = 0
        self.skipped_lines = 0
        self.processor = processor
        self.input = input
        self.varIdx = varIdx
        self.encoding = encoding
        self.logger = logger

    def records(self): 
        first = True
        line_no = 0
        with openFile(self.input) as input_file:
            for line in input_file:
                line_no += 1
                line = line.decode(self.encoding)
                try:
                    if line.startswith('#'):
                        continue
                    for bins,rec in self.processor.process(line):
                        if first:
                            self.columnRange = self.processor.columnRange
                            first = False
                        self.num_records += 1
                        if self.varIdx is not None:
                            var_key = (rec[0], rec[2], rec[3])
                            if var_key not in self.varIdx or rec[1] not in self.varIdx[var_key]:
                                continue
                        yield (line_no, bins, rec)
                except Exception as e:
                    self.logger.debug('Failed to process line "{}...": {}'.format(line[:20].strip(), e))
                    self.skipped_lines += 1

class StandaloneTextReader:
    #
    # This processor fire up 1 worker to read an input file
    # and gather their outputs
    #
    def __init__(self, processor, input, varIdx, encoding, logger):
        self.num_records = 0
        self.skipped_lines = 0
        #
        self.reader, w = Pipe(False)
        self.worker = TextWorker(processor, input, varIdx, w, 1, 0, encoding, logger)
        self.worker.start()
        # the send value is columnRange
        self.columnRange = self.reader.recv()
        
    def records(self):
        while True:
            val = self.reader.recv()
            if val is None:
                self.num_records, self.skipped_lines = self.reader.recv()
                break
            else:
                yield val
        self.worker.join()

class MultiTextReader:
    #
    # This processor fire up num workers to read an input file
    # and gather their outputs
    #
    def __init__(self, processor, input, varIdx, jobs, encoding, logger):
        self.readers = []
        self.workers = []
        self.num_records = 0
        self.skipped_lines = 0
        for i in range(jobs):
            r, w = Pipe(False)
            p = TextWorker(processor, input, varIdx, w, jobs, i, encoding, logger)
            self.readers.append(r)
            self.workers.append(p)
            p.start()
        # the send value is columnRange
        for reader in self.readers:
            self.columnRange = reader.recv()
        
    def records(self):
        all_workers = len(self.readers)
        still_working = len(self.readers)
        #
        # we need a heap to keep records read from multiple processes in order
        # we can not really guarantee this if there are large trunks of ignored
        # records but a heap size = 4 * number of readers should work in most cases
        #
        heap = []
        filled = False
        while True:
            for idx, reader in enumerate(self.readers):
                val = reader.recv()
                if val is None:
                    # one thread died ...
                    still_working -= 1
                    nr, sl = reader.recv()
                    self.num_records += nr
                    self.skipped_lines += sl
                    self.readers[idx] = None
                elif filled:
                    yield heappushpop(heap, val)
                else:
                    heappush(heap, val)
                    filled = len(heap) == 4 * len(self.readers)
            if still_working < all_workers:
                self.readers = [x for x in self.readers if x is not None]
                all_workers = len(self.readers)
                if all_workers == 0:
                    # return all things in the heap
                    for i in range(len(heap)):
                        yield heappop(heap)
                    break
        for p in self.workers:
            p.join()

#     def run1(self):
#         # this is a hold for the merge_by_col feature which is disabled for now
#         rec_key = []
#         rec_stack = []
#         for line in input_file:
#             line = line.decode()
#             try:
#                 if line.startswith('#'):
#                     continue
#                 self.processed_lines += 1
#                 tokens = [x.strip() for x in line.split(self.delimiter)]
#                 key = [tokens(x) for x in self.merge_by_cols]
#                 if not rec_stack:
#                     rec_key = key
#                     rec_stack.append(tokens)
#                     continue
#                 # if the same, wait fot the next record
#                 elif rec_key == key:
#                     rec_stack.append(tokens)
#                     continue
#                 # if not the same, ...
#                 elif len(rec_stack) == 1:
#                     # use the value in stack
#                     line = rec_stack[0]
#                     rec_stack[0] = tokens
#                     rec_key = key
#                 # if multiple
#                 else:
#                     n = len(rec_stack)
#                     # merge values
#                     line = [rec_stack[0][x] if x in self.merge_by_cols else \
#                         ','.join([rec_stack[i][x] for i in range(n)]) for x in range(len(tokens))]
#                     rec_stack[0] = tokens
#                     rec_key = key
#                 #
#                 for bins,rec in self.process(line):
#                     self.num_records += 1
#                     yield bins, rec
#             except Exception as e:
#                 self.logger.debug('Failed to process line "{}...": {}'.format(line[:20].strip(), e))
#                 self.skipped_lines += 1

#
# Import data
#
#

class BaseImporter:
    '''A general class for importing variants'''
    def __init__(self, proj, files, build, force, mode='insert'):
        self.proj = proj
        self.db = proj.db
        self.logger = proj.logger
        self.mode = mode
        self.sample_in_file = []
        #
        if len(files) == 0:
            raise IOError('Please specify the filename of the input data.')
            sys.exit(1)
        #
        if mode == 'insert':
            self.files = []
            cur = self.db.cursor()
            cur.execute('SELECT filename from filename;')
            existing_files = [x[0] for x in cur.fetchall()]
            for filename in files:
                if filename in existing_files:
                    if force:
                        self.logger.info('Re-importing imported file {}'.format(filename))
                        IDs = proj.selectSampleByPhenotype('filename = "{}"'.format(filename))
                        self.proj.db.attach(self.proj.name + '_genotype')
                        proj.removeSamples(IDs)
                        self.proj.db.detach(self.proj.name + '_genotype')
                        # remove file record
                        cur = self.db.cursor()
                        cur.execute('DELETE FROM filename WHERE filename={};'.format(self.db.PH), (filename,))
                        self.db.commit()
                        self.files.append(filename)
                    else:
                        self.logger.info('Ignoring imported file {}'.format(filename))
                elif not os.path.isfile(filename):
                    raise ValueError('File {} does not exist'.format(filename))
                else:
                    self.files.append(filename)
        else:
            for filename in files:
                if not os.path.isfile(filename):
                    raise ValueError('File {} does not exist'.format(filename))
            self.files = files
        # for #record, #genotype (new or updated), #new variant, SNV, insertion, deletion, complex variants, invalid record, updated record
        self.count = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.total_count = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.import_alt_build = False
        if len(self.files) == 0:
            raise ValueError('No file to import')
        #
        if build is None:
            if self.proj.build is not None:
                self.build = self.proj.build
                self.logger.info('Using primary reference genome {} of the project.'.format(self.build))
            else:
                self.build = self.guessBuild(self.files[0])
                if self.build is None:
                    raise ValueError('Cannot determine a reference genome from files provided. Please specify it using parameter --build')
                else:
                    self.logger.info('Reference genome is determined to be {}'.format(self.build))
        else:
            self.build = build
        #
        if self.proj.build is None:
            if mode == 'insert':
                self.proj.setRefGenome(self.build)
            else:
                raise ValueError('Cannot update variants of a project without variants.')
        elif self.build == self.proj.build:
            # perfect case
            pass
        elif self.build == self.proj.alt_build:
            # troublesome
            self.import_alt_build = True
        elif self.proj.alt_build is None:
            # even more troublesome
            self.logger.warning('The new files uses a different refrence genome ({}) from the primary reference genome ({}) of the project.'.format(self.build, self.proj.build))
            self.logger.info('Adding an alternative reference genome ({}) to the project.'.format(self.build))
            tool = LiftOverTool(self.proj)
            # in case of insert, the indexes will be dropped soon so do not build
            # index now
            tool.setAltRefGenome(self.build, build_index= (mode != 'insert'))
            self.import_alt_build = True

    def __del__(self):
        if self.mode == 'insert':
            self.proj.createIndexOnMasterVariantTable()

    def guessBuild(self, file):
        # by default, reference genome cannot be determined from file
        return None

    def createLocalVariantIndex(self, table='variant'):
        '''Create index on variant (chr, pos, ref, alt) -> variant_id'''
        self.variantIndex = {}
        cur = self.db.cursor()
        numVariants = self.db.numOfRows(table)
        if numVariants == 0:
            return
        self.logger.debug('Creating local indexes for {:,} variants'.format(numVariants));
        where_clause = 'WHERE variant_id IN (SELECT variant_id FROM {})'.format(table) if table != 'variant' else ''
        if self.import_alt_build:
            cur.execute('SELECT variant_id, alt_chr, alt_pos, ref, alt FROM variant {};'.format(where_clause))
        else:
            cur.execute('SELECT variant_id, chr, pos, ref, alt FROM variant {};'.format(where_clause))
        prog = ProgressBar('Getting existing variants', numVariants)
        for count, rec in enumerate(cur):
            # zero for existing loci
            key = (rec[1], rec[3], rec[4])
            if key in self.variantIndex:
                self.variantIndex[key][rec[2]] = (rec[0], 0)
            else:
                self.variantIndex[key] = {rec[2]: (rec[0], 0)}
            #self.variantIndex[(rec[1], rec[3], rec[4])][rec[2]] = (rec[0], 0)
            if count % self.db.batch == 0:
                prog.update(count)
        prog.done()

    def getSampleName(self, filename, prober):
        '''Prove text file for sample name'''
        header_line = None
        count = 0
        with openFile(filename) as input:
            for line in input:
                line = line.decode(self.encoding)
                # the last # line
                if line.startswith('#'):
                    header_line = line
                else:
                    try:
                        for bins, rec in prober.process(line):
                            if header_line is None:
                                return len(rec), []
                            elif len(rec) == 0:
                                return 0, []
                            else:
                                cols = [x[0] for x in prober.fields]
                                if type(cols[0]) is tuple:
                                    fixed = False
                                    # mutiple ones, need to figure out the moving one
                                    for i,idx in enumerate(prober.raw_fields[0].index.split(',')):
                                        if ':' in idx:
                                            cols = [x[i] for x in cols]
                                            fixed = True
                                            break
                                    if not fixed:
                                        cols = [x[-1] for x in cols]
                                header = [x.strip() for x in header_line.split()] # #prober.delimiter)]
                                if max(cols) - min(cols)  < len(header) and len(header) > max(cols):
                                    return len(rec), [header[len(header) - prober.nColumns + x] for x in cols]
                                else:
                                    return len(rec), []
                    except IgnoredRecord:
                        continue
                    except Exception as e:
                        # perhaps not start with #, if we have no header, use it anyway
                        if header_line is None:
                            header_line = line
                        count += 1
                        if count == 100:
                            raise ValueError('No genotype column could be determined after 1000 lines.')
                        self.logger.debug(e)

    def recordFileAndSample(self, filename, sampleNames):
        cur = self.db.cursor()
        # get header of file
        header = ''
        with openFile(filename) as input:
            for line in input:
                line = line.decode(self.encoding)
                if line.startswith('#'):
                    header += line
                else:
                    break
        cur.execute("INSERT INTO filename (filename, header) VALUES ({0}, {0});".format(self.db.PH), (filename, header))
        filenameID = cur.lastrowid
        sample_ids = []
        s = delayedAction(self.logger.info, 'Creating {} genotype tables'.format(len(sampleNames)))
        #
        for samplename in sampleNames:
            cur.execute('INSERT INTO sample (file_id, sample_name) VALUES ({0}, {0});'.format(self.db.PH),
                (filenameID, samplename))
            sid = cur.lastrowid
            sample_ids.append(sid)
        del s
        return sample_ids

    def importData(self):
        '''Start importing'''
        sample_in_files = []
        for count,f in enumerate(self.files):
            self.logger.info('{} variants from {} ({}/{})'.format('Importing' if self.mode == 'insert' else 'Updating', f, count + 1, len(self.files)))
            self.importFromFile(f)
            if self.mode == 'insert':
                total_var = sum(self.count[3:7])
                self.logger.info('{:,} variants ({:,} new{}) from {:,} lines are imported, {}.'\
                    .format(total_var, self.count[2],
                        ''.join([', {:,} {}'.format(x, y) for x, y in \
                            zip(self.count[3:8], ['SNVs', 'insertions', 'deletions', 'complex variants', 'invalid']) if x > 0]),
                        self.count[0],
                        'no sample is created' if len(self.sample_in_file) == 0 else 'with a total of {:,} genotypes from {}'.format(
                            self.count[1], 'sample {}'.format(self.sample_in_file[0]) if len(self.sample_in_file) == 1 else '{:,} samples'.format(len(self.sample_in_file)))))
            else:
                self.logger.info('Field{} {} of {:,} variants{} are updated'.format('' if len(self.variant_info) == 1 else 's', ', '.join(self.variant_info), self.count[8],
                    '' if self.count[1] == 0 else ' and geno fields of {:,} genotypes'.format(self.count[1])))
            for i in range(len(self.count)):
                self.total_count[i] += self.count[i]
                self.count[i] = 0
            sample_in_files.extend(self.sample_in_file)
        if len(self.files) > 1:
            if self.mode == 'insert':
                total_var = sum(self.total_count[3:7])
                self.logger.info('{:,} variants ({:,} new{}) from {:,} lines are imported, {}.'\
                    .format(total_var, self.total_count[2],
                        ''.join([', {:,} {}'.format(x, y) for x, y in \
                            zip(self.total_count[3:8], ['SNVs', 'insertions', 'deletions', 'complex variants', 'invalid']) if x > 0]),
                        self.total_count[0],
                        'no sample is created' if len(sample_in_files) == 0 else 'with a total of {:,} genotypes from {}'.format(
                            self.total_count[1], 'sample {}'.format(sample_in_files[0]) if len(sample_in_files) == 1 else '{:,} samples'.format(len(sample_in_files)))))
            else:
                self.logger.info('Field{} {} of {:,} variants{} are updated'.format('' if len(self.variant_info) == 1 else 's', ', '.join(self.variant_info), self.total_count[8],
                    '' if self.total_count[1] == 0 else ' and geno fields of {:,} genotypes'.format(self.total_count[1])))

    def finalize(self):
        # this function will only be called from import
        cur = self.db.cursor()
        total_new = sum(self.total_count[3:7])
        if total_new > 0:
            # analyze project to get correct number of rows for the master variant table
            self.proj.analyze(force=True)
        if total_new == 0 or self.proj.alt_build is None:
            # if no new variant, or no alternative reference genome, do nothing
            return
        # we need to run lift over to convert coordinates before importing data.
        tool = LiftOverTool(self.proj)
        to_be_mapped = os.path.join(self.proj.temp_dir, 'var_in.bed')
        loci_count = 0
        with open(to_be_mapped, 'w') as output:
            for key in self.variantIndex:
                for pos, status in self.variantIndex[key].iteritems():
                    if status[1] == 1:
                        output.write('{0}\t{1}\t{2}\t{3}/{4}/{5}\n'.format(key[0] if len(key[0]) > 2 else 'chr' + key[0],
                           pos - 1, pos, key[1], key[2], status[0]))
                        loci_count += 1
        # free some RAM
        self.variantIndex.clear()
        #
        if self.import_alt_build:
            self.logger.info('Mapping new variants at {} loci from {} to {} reference genome'.format(loci_count, self.proj.alt_build, self.proj.build))
            query = 'UPDATE variant SET bin={0}, chr={0}, pos={0} WHERE variant_id={0};'.format(self.db.PH)
            mapped_file, err_count = tool.mapCoordinates(to_be_mapped, self.proj.alt_build, self.proj.build)
        else:
            self.logger.info('Mapping new variants at {} loci from {} to {} reference genome'.format(loci_count, self.proj.build, self.proj.alt_build))
            query = 'UPDATE variant SET alt_bin={0}, alt_chr={0}, alt_pos={0} WHERE variant_id={0};'.format(self.db.PH)
            # this should not really happen, but people (like me) might manually mess up with the database
            s = delayedAction(self.logger.info, 'Adding alternative reference genome {} to the project.'.format(self.proj.alt_build))
            headers = self.db.getHeaders('variant')
            for fldName, fldType in [('alt_bin', 'INT'), ('alt_chr', 'VARCHAR(20)'), ('alt_pos', 'INT')]:
                if fldName in headers:
                    continue
                self.db.execute('ALTER TABLE variant ADD {} {} NULL;'.format(fldName, fldType))
            del s
            mapped_file, err_count = tool.mapCoordinates(to_be_mapped, self.proj.build, self.proj.alt_build)
        # update records
        prog = ProgressBar('Updating coordinates', total_new)
        # 1: succ mapped
        count = 0
        with open(mapped_file) as var_mapped:
            for line in var_mapped.readlines():
                try:
                    chr, start, end, name = line.strip().split()
                    ref, alt, var_id = name.split('/')
                    if chr.startswith('chr'):
                        chr = chr[3:]
                    pos = int(start) + 1
                    var_id = int(var_id)
                except:
                    continue
                cur.execute(query, (getMaxUcscBin(pos - 1, pos), chr, pos, var_id))
                count += 1
                if count % self.db.batch == 0:
                    self.db.commit()
                    prog.update(count)
        self.db.commit()
        prog.done()
        self.logger.info('Coordinates of {} ({} total, {} failed to map) new variants are updated.'\
            .format(count, total_new, err_count))
            

class TextImporter(BaseImporter):
    '''Import variants from one or more tab or comma separated files.'''
    def __init__(self, proj, files, build, format, sample_name=None, 
        force=False, jobs=1, fmt_args=[]):
        BaseImporter.__init__(self, proj, files, build, force, mode='insert')
        self.jobs = max(1, jobs)
        # we cannot guess build information from txt files
        if build is None and self.proj.build is None:
            raise ValueError('Please specify the reference genome of the input data.')
        #
        # try to guess file type
        if not format:
            filename = self.files[0].lower()
            if filename.endswith('.vcf') or filename.endswith('.vcf.gz'):
                format = 'vcf'
            else:
                raise ValueError('Cannot guess input file type from filename')
        try:
            fmt = fileFMT(format, fmt_args, logger=self.logger)
        except Exception as e:
            self.logger.debug(e)
            raise IndexError('Unrecognized input format: {}\nPlease check your input parameters or configuration file *{}* '.format(e, format))
        #
        self.sample_name = sample_name
        #
        # how to split processed records
        self.ranges = fmt.ranges
        self.variant_fields = [x.name for x in fmt.fields[fmt.ranges[0]:fmt.ranges[1]]]
        self.variant_info = [x.name for x in fmt.fields[fmt.ranges[1]:fmt.ranges[2]]]
        self.genotype_field = [x.name for x in fmt.fields[fmt.ranges[2]:fmt.ranges[3]]]
        self.genotype_info = [x for x in fmt.fields[fmt.ranges[3]:fmt.ranges[4]]]
        #
        if fmt.input_type == 'variant':
            # process variants, the fields for pos, ref, alt are 1, 2, 3 in fields.
            self.processor = LineImporter(fmt.fields, [(1, 2, 3)], fmt.delimiter, fmt.merge_by_cols, self.logger)
        else:  # position or range type
            raise ValueError('Can only import data with full variant information (chr, pos, ref, alt)')
        # probe number of sample
        if self.genotype_field:
            self.prober = LineImporter([fmt.fields[fmt.ranges[2]]], [], fmt.delimiter, None, self.logger)
        # there are variant_info
        if self.variant_info:
            cur = self.db.cursor()
            headers = self.db.getHeaders('variant')
            for f in fmt.fields[fmt.ranges[1]:fmt.ranges[2]]:
                # either insert or update, the fields must be in the master variant table
                self.proj.checkFieldName(f.name, exclude='variant')
                if f.name not in headers:
                    s = delayedAction(self.logger.info, 'Adding column {}'.format(f.name))
                    cur.execute('ALTER TABLE variant ADD {} {};'.format(f.name, f.type))
                    del s
        #
        if fmt.input_type != 'variant':
            self.logger.info('Only variant input types that specifies fields for chr, pos, ref, alt could be imported.')
        #
        self.input_type = fmt.input_type
        self.encoding = fmt.encoding
        fbin, fchr, fpos = ('alt_bin', 'alt_chr', 'alt_pos') if self.import_alt_build else ('bin', 'chr', 'pos')
        self.update_variant_query = 'UPDATE variant SET {0} WHERE variant.variant_id = {1};'\
            .format(', '.join(['{}={}'.format(x, self.db.PH) for x in self.variant_info]), self.db.PH)
        self.variant_insert_query = 'INSERT INTO variant ({0}, {1}, {2}, ref, alt {3}) VALUES ({4});'\
            .format(fbin, fchr, fpos, ' '.join([', ' + x for x in self.variant_info]), ', '.join([self.db.PH]*(len(self.variant_info) + 5)))
        #
        self.createLocalVariantIndex()
        # drop index here after all possible exceptions have been raised.
        self.proj.dropIndexOnMasterVariantTable()
                    
    def addVariant(self, cur, rec):
        #
        if rec[4] == '-':
            self.count[5] += 1
        elif rec[3] == '-':
            self.count[4] += 1
        elif len(rec[4]) == 1 and len(rec[3]) == 1:
            self.count[3] += 1
        else:
            self.count[6] += 1
        var_key = tuple((rec[1], rec[3], rec[4]))
        if var_key in self.variantIndex and rec[2] in self.variantIndex[var_key]:
            variant_id = self.variantIndex[var_key][rec[2]][0]
            if len(rec) > 5:
                self.count[8] += 1
                cur.execute(self.update_variant_query, rec[5:] + [variant_id])
            return variant_id
        else:
            # new varaint!
            # alt_chr and alt_pos are updated if adding by alternative reference genome
            self.count[2] += 1
            cur.execute(self.variant_insert_query, rec)
            variant_id = cur.lastrowid
            # one for new variant
            if var_key in self.variantIndex:
                self.variantIndex[var_key][rec[2]] = (variant_id, 1)
            else:
                self.variantIndex[var_key] = {rec[2]: (variant_id, 1)}
            return variant_id

    def getSampleIDs(self, input_filename):
        if not self.sample_name:
            # if no sample name is specified
            if not self.genotype_field:
                self.logger.warning('Sample information is not recorded for a file without genotype and sample name.')
                self.sample_in_file = []
                return []
            else:
                try:
                    numSample, names = self.getSampleName(input_filename, self.prober)
                    if not names:
                        if numSample == 1:
                            self.logger.debug('Missing sample name (name None is used)'.format(numSample))
                            self.sample_in_file = [None]
                            return self.recordFileAndSample(input_filename, [None])
                        elif numSample == 0:
                            self.logger.debug('No genotype column exists in the input file so no sample will be recorded.')
                            self.sample_in_file = []
                            return []
                        else:
                            raise ValueError('Failed to guess sample name. Please specify sample names for {} samples using parameter --sample_name, or add a proper header to your input file. See "vtools import_variants -h" for details.'.format(numSample))
                    else:
                        self.sample_in_file = [x for x in names]
                        return self.recordFileAndSample(input_filename, names)
                except ValueError:
                    # cannot find any genotype column, perhaps no genotype is defined in the file (which is allowed)
                    self.logger.warning('No genotype column could be found from the input file. Assuming no genotype.')
                    self.sample_in_file = []
                    return []
        else:
            self.sample_in_file = [x for x in self.sample_name]
            if not self.genotype_field:
                # if no genotype, but a sample name is given
                self.logger.debug('Input file does not contain any genotype. Only the variant ownership information is recorded.')
                return self.recordFileAndSample(input_filename, self.sample_name)
            else:
                try:
                    numSample, names = self.getSampleName(input_filename, self.prober)
                except ValueError as e:
                    self.logger.debug(e)
                    numSample = 0
                #
                if numSample == 0:
                    self.logger.warning('No genotype column could be found from the input file. Assuming no genotype.')
                    self.genotype_field = []
                    self.genotype_info = []
                    # remove genotype field from processor
                    self.processor.reset(validTill=self.ranges[2])
                    if len(self.sample_name) > 1:
                        raise ValueError("When there is no sample genotype, only one sample name is allowed.")
                elif len(self.sample_name) != numSample:
                    raise ValueError('{} sample detected but only {} sample names are specified'.format(numSample, len(self.sample_name)))                        
                return self.recordFileAndSample(input_filename, self.sample_name)
 
    def importFromFile(self, input_filename):
        '''Import a TSV file to sample_variant'''
        # reset text processor to allow the input of files with different number of columns
        self.processor.reset()
        if self.genotype_field:
            self.prober.reset()
        #
        sample_ids = self.getSampleIDs(input_filename)
        #
        cur = self.db.cursor()
        # cache genotype status
        if len(sample_ids) > 0 and len(self.genotype_field) > 0:
            # has genotype
            genotype_status = 1
        elif len(sample_ids) > 0:
            # no genotype but with sample
            genotype_status = 2
        else:
            # no genotype no sample
            genotype_status = 0
        lc = lineCount(input_filename, self.encoding)
        update_after = min(max(lc//200, 100), 100000)
        # one process is for the main program, the
        # other threads will handle input
        reader = TextReader(self.processor, input_filename, None, self.jobs - 1, self.encoding, self.logger)
        if genotype_status != 0:
            writer = GenotypeWriter(self.proj, self.genotype_field, self.genotype_info,
                sample_ids)
        # preprocess data
        prog = ProgressBar(os.path.split(input_filename)[-1], lc)
        last_count = 0
        fld_cols = None
        for self.count[0], bins, rec in reader.records():
            variant_id = self.addVariant(cur, bins + rec[0:self.ranges[2]])
            if genotype_status == 1:
                if fld_cols is None:
                    col_rngs = [reader.columnRange[x] for x in range(self.ranges[2], self.ranges[4])]
                    fld_cols = []
                    for idx in range(len(sample_ids)):
                        fld_cols.append([sc + (0 if sc + 1 == ec else idx) for sc,ec in col_rngs])
                    if col_rngs[0][1] - col_rngs[0][0] != len(sample_ids):
                        self.logger.error('Number of genotypes ({}) does not match number of samples ({})'.format(
                            col_rngs[0][1] - col_rngs[0][0], len(sample_ids)))
                for idx, id in enumerate(sample_ids):
                    if rec[self.ranges[2] + idx] is not None:
                        self.count[1] += 1
                        writer.write(id, [variant_id] + [rec[c] for c in fld_cols[idx]])
            elif genotype_status == 2:
                # should have only one sample
                for id in sample_ids:
                    writer.write(id, [variant_id])
            if (last_count == 0 and self.count[0] > 200) or (self.count[0] - last_count > update_after):
                self.db.commit()
                last_count = self.count[0]
                prog.update(self.count[0])
        prog.done()
        self.count[7] = reader.skipped_lines
        # stop writers
        if genotype_status != 0:
            writer.close()
        self.db.commit()
       
class TextUpdater(BaseImporter):
    '''Import variants from one or more tab or comma separated files.'''
    def __init__(self, proj, table, files, build, format, jobs, fmt_args=[]):
        # if update is None, recreate index
        BaseImporter.__init__(self, proj, files, build, True, mode='update')
        #
        self.jobs = max(1, jobs)
        if not proj.isVariantTable(table):
            raise ValueError('Variant table {} does not exist.'.format(table))
        # we cannot guess build information from txt files
        if build is None and self.proj.build is None:
            raise ValueError('Please specify the reference genome of the input data.')
        #
        # try to guess file type
        if not format:
            filename = self.files[0].lower()
            if filename.endswith('.vcf') or filename.endswith('.vcf.gz'):
                format = 'vcf'
            else:
                raise ValueError('Cannot guess input file type from filename')
        try:
            fmt = fileFMT(format, fmt_args, logger=self.logger)
        except Exception as e:
            self.logger.debug(e)
            raise IndexError('Unrecognized input format: {}\nPlease check your input parameters or configuration file *{}* '.format(e, format))
        #
        # how to split processed records
        self.ranges = fmt.ranges
        self.variant_fields = [x.name for x in fmt.fields[fmt.ranges[0]:fmt.ranges[1]]]
        self.variant_info = [x.name for x in fmt.fields[fmt.ranges[1]:fmt.ranges[2]]]
        self.genotype_field = [x.name for x in fmt.fields[fmt.ranges[2]:fmt.ranges[3]]]
        self.genotype_info = [x for x in fmt.fields[fmt.ranges[3]:fmt.ranges[4]]]
        #
        if not self.variant_info and not self.genotype_info:
            raise ValueError('No variant or genotype info needs to be updated')
        #
        if fmt.input_type == 'variant':
            # process variants, the fields for pos, ref, alt are 1, 2, 3 in fields.
            self.processor = LineImporter(fmt.fields, [(1, 2, 3)], fmt.delimiter, fmt.merge_by_cols, self.logger)
        else:  # position or range type
            self.processor = LineImporter(fmt.fields, [(1,)], fmt.delimiter, fmt.merge_by_cols, self.logger)
        # probe number of sample
        if self.genotype_field and self.genotype_info:
            self.prober = LineImporter([fmt.fields[fmt.ranges[2]]], [], fmt.delimiter, None, self.logger)
        # there are variant_info
        if self.variant_info:
            cur = self.db.cursor()
            headers = self.db.getHeaders('variant')
            for f in fmt.fields[fmt.ranges[1]:fmt.ranges[2]]:
                # either insert or update, the fields must be in the master variant table
                self.proj.checkFieldName(f.name, exclude='variant')
                if f.name not in headers:
                    s = delayedAction(self.logger.info, 'Adding column {}'.format(f.name))
                    cur.execute('ALTER TABLE variant ADD {} {};'.format(f.name, f.type))
                    del s
        #if len(self.variant_info) == 0 and len(self.genotype_info == 0:
        #    raise ValueError('No field could be updated using this input file')
        #
        self.input_type = fmt.input_type
        self.encoding = fmt.encoding
        fbin, fchr, fpos = ('alt_bin', 'alt_chr', 'alt_pos') if self.import_alt_build else ('bin', 'chr', 'pos')
        from_table = 'AND variant.variant_id IN (SELECT variant_id FROM {})'.format(table) if table != 'variant' else ''
        self.update_variant_query = 'UPDATE variant SET {0} WHERE variant.variant_id = {1};'\
            .format(', '.join(['{}={}'.format(x, self.db.PH) for x in self.variant_info]), self.db.PH)
        self.update_position_query = 'UPDATE variant SET {1} WHERE variant.{2} = {0} AND variant.{3} = {0} AND variant.{4} = {0} {5};'\
            .format(self.db.PH, ', '.join(['{}={}'.format(x, self.db.PH) for x in self.variant_info]), fbin, fchr, fpos, from_table)
        self.update_range_query = 'UPDATE variant SET {1} WHERE variant.{2} = {0} AND variant.{3} = {0} AND variant.{4} >= {0} AND variant.{4} <= {0} {5};'\
            .format(self.db.PH, ', '.join(['{}={}'.format(x, self.db.PH) for x in self.variant_info]), fbin, fchr, fpos, from_table)
        #
        self.createLocalVariantIndex(table)
        self.table = table

    def updateVariant(self, cur, bins, rec):
        if self.input_type == 'variant':
            var_key = (rec[0], rec[2], rec[3])
            if var_key in self.variantIndex and rec[1] in self.variantIndex[var_key]:
                variant_id = self.variantIndex[var_key][rec[1]][0]
                # update by variant_id, do not need bins
                if len(rec) > 4:
                    cur.execute(self.update_variant_query, rec[4:] + [variant_id])
                    self.count[8] += cur.rowcount
                return variant_id
        elif self.input_type == 'position':
            cur.execute(self.update_position_query, rec[2:] + bins + [rec[0], rec[1]])
            self.count[8] += cur.rowcount
        else:  # range based
            cur.execute(self.update_range_query, rec[3:] + bins + [rec[0], rec[1], rec[2]])
            self.count[8] += cur.rowcount
        return None

    def getSampleIDs(self, filename):
        if not self.genotype_field:
            # no genotype_field, good, do not have to worry about genotype
            return []
        # has the file been imported before?
        cur = self.db.cursor()
        cur.execute('SELECT filename from filename;')
        existing_files = [x[0] for x in cur.fetchall()]
        if filename not in existing_files:
            return []
        #
        # what are the samples related to this file?
        cur.execute('SELECT sample_id, sample_name FROM sample LEFT OUTER JOIN filename ON sample.file_id = filename.file_id WHERE filename.filename = {}'\
            .format(self.db.PH), (filename,))
        sample_ids = []
        sample_names = []
        for rec in cur:
            sample_ids.append(rec[0])
            sample_names.append(rec[1])
        # what is the sample names get from this file?
        nSample, names = self.getSampleName(filename, self.prober)
        if nSample != len(sample_ids):
            self.logger.warning('Number of samples mismatch. Cannot update genotype')
            return []
        if nSample == 1:
            # if only one sample, update it regardless of sample name.
            return sample_ids
        if sample_names == names:
            # if sample name matches, get sample_ids
            return sample_ids
        else:
            self.logger.warning('Sample names mismatch. Cannot update genotype.')
            return []
        
    def importFromFile(self, input_filename):
        '''Import a TSV file to sample_variant'''
        self.processor.reset()
        if self.genotype_field and self.genotype_info:
            self.prober.reset()
        #
        # do we handle genotype info as well?
        sample_ids = self.getSampleIDs(input_filename) if self.genotype_info else []
        # one process is for the main program, the
        # other thread will handle input
        reader = TextReader(self.processor, input_filename,
            # in the case of variant, we filter from the reading stage to save some time
            None if (self.table == 'variant' or self.input_type != 'variant') else self.variantIndex,
            self.jobs - 1, self.encoding, self.logger)
        #
        # do we need to add extra columns to the genotype tables
        if sample_ids:
            s = delayedAction(self.logger.info, 'Preparing genotype tables (adding needed fields and indexes)...')
            cur = self.db.cursor()
            for id in sample_ids:
                headers = [x.upper() for x in self.db.getHeaders('{}_genotype.genotype_{}'.format(self.proj.name, id))]
                if 'GT' not in headers:  # for genotype
                    self.logger.debug('Adding column GT to table genotype_{}'.format(id))
                    cur.execute('ALTER TABLE {}_genotype.genotype_{} ADD {} {};'.format(self.proj.name, id, 'GT', 'INT'))
                for field in self.genotype_info:
                    if field.name.upper() not in headers:
                        self.logger.debug('Adding column {} to table genotype_{}'.format(field.name, id))
                        cur.execute('ALTER TABLE {}_genotype.genotype_{} ADD {} {};'.format(self.proj.name, id, field.name, field.type))
            # if we are updating by variant_id, we will need to create an index for it
            for id in sample_ids:
                if not self.db.hasIndex('{0}_genotype.genotype_{1}_index'.format(self.proj.name, id)):
                    cur.execute('CREATE INDEX {0}_genotype.genotype_{1}_index ON genotype_{1} (variant_id ASC)'.format(self.proj.name, id))
            del s
            genotype_update_query = {id: 'UPDATE {0}_genotype.genotype_{1} SET {2} WHERE variant_id = {3};'\
                .format(self.proj.name, id,
                ', '.join(['{}={}'.format(x, self.db.PH) for x in [y.name for y in self.genotype_info]]),
                self.db.PH)
                for id in sample_ids}
        else:
            # do not import genotype even if the input file has them
            self.genotype_field = []
            self.genotype_info = []
            self.processor.reset(validTill=self.ranges[2])
        #
        cur = self.db.cursor()
        lc = lineCount(input_filename, self.encoding)
        update_after = min(max(lc//200, 100), 100000)
        fld_cols = None
        prog = ProgressBar(os.path.split(input_filename)[-1], lc)
        last_count = 0
        for self.count[0], bins, rec in reader.records():
            variant_id = self.updateVariant(cur, bins, rec[0:self.ranges[2]])
            # variant might not exist
            if variant_id is not None and sample_ids:
                if fld_cols is None:
                    col_rngs = [reader.columnRange[x] for x in range(self.ranges[3], self.ranges[4])]
                    fld_cols = []
                    for idx in range(len(sample_ids)):
                        fld_cols.append([sc + (0 if sc + 1 == ec else idx) for sc,ec in col_rngs])
                    if col_rngs[0][1] - col_rngs[0][0] != len(sample_ids):
                        self.logger.error('Number of genotypes ({}) does not match number of samples ({})'.format(
                            col_rngs[0][1] - col_rngs[0][0], len(sample_ids)))
                for idx, id in enumerate(sample_ids):
                    if rec[self.ranges[2] + idx] is not None:
                        cur.execute(genotype_update_query[id], [rec[c] for c in fld_cols[idx]] + [variant_id])
                        self.count[1] += 1
            if self.count[0] - last_count > update_after:
                last_count = self.count[0]
                self.db.commit()
                prog.update(self.count[0])
        self.count[7] = reader.skipped_lines
        self.db.commit()
        prog.done(self.count[0])

#
#
# Functions provided by this script
#
#

def importVariantsArguments(parser):
    parser.add_argument('input_files', nargs='+',
        help='''A list of files that will be imported. The file should be delimiter
            separated with format described by parameter --format. Gzipped files are
            acceptable.''')
    parser.add_argument('--build',
        help='''Build version of the reference genome (e.g. hg18) of the input data. If
            unspecified, it is assumed to be the primary reference genome of the project.
            If a reference genome that is different from the primary reference genome of the
            project is specified, it will become the alternative reference genome of the
            project. The UCSC liftover tool will be automatically called to map input
            coordinates between the primary and alternative reference genomes.''')
    parser.add_argument('--format',
        help='''Format of the input text file. It can be one of the variant tools
            supported file types such as VCF (cf. 'vtools show formats'), or a 
            local format specification file (with extension .fmt). If unspecified,
            variant tools will try to guess format from file extension. Some file
            formats accept parameters (cf. 'vtools show format FMT') and allow you
            to import additional or alternative fields defined for the format. ''')
    parser.add_argument('--sample_name', nargs='*', default=[],
        help='''Name of the samples imported by the input files. The same names will be
            used for all files if multiple files are imported. If unspecified, headers
            of the genotype columns of the last comment line (line starts with #) of the
            input files will be used (and thus allow different sample names for input files).
            If sample names are specified for input files without genotype, samples
            will be created without genotype. If sample names cannot be determined from
            input file and their is no ambiguity (only one sample is imported), a sample
            with NULL sample name will be created.''')
    parser.add_argument('-f', '--force', action='store_true',
        help='''Import files even if the files have been imported before. This option
            can be used to import from updated file or continue disrupted import, but will
            not remove wrongfully imported variants from the master variant table.'''),
    parser.add_argument('-j', '--jobs', metavar='N', default=1, type=int,
        help='''Number of processes to import input file. Variant tools by default
            uses a single process for reading and writing, and can use one or more
            dedicated reader processes (jobs=2 or more) to process input files. Due
            to the overhead of inter-process communication, more jobs do not
            automatically lead to better performance.''')

def importVariants(args):
    try:
        with Project(verbosity=args.verbosity) as proj:
            importer = TextImporter(proj=proj, files=args.input_files,
                build=args.build, format=args.format, sample_name=args.sample_name,
                force=args.force, jobs=args.jobs, fmt_args=args.unknown_args)
            importer.importData()
            importer.finalize()
        proj.close()
    except Exception as e:
        sys.exit(e)


def setFieldValue(proj, table, items, build):
    # fields
    expr = ','.join([x.split('=',1)[1] for x in items])
    select_clause, fields = consolidateFieldName(proj, table, expr,
        build and build == proj.alt_build)
    #
    # FROM clause
    from_clause = 'FROM {} '.format(table)
    fields_info = sum([proj.linkFieldToTable(x, table) for x in fields], [])
    #
    processed = set()
    for tbl, conn in [(x.table, x.link) for x in fields_info if x.table != '']:
        if (tbl.lower(), conn.lower()) not in processed:
            from_clause += ' LEFT OUTER JOIN {} ON {}'.format(tbl, conn)
            processed.add((tbl.lower(), conn.lower()))
    # running query
    cur = proj.db.cursor()
    #
    if 'LEFT OUTER JOIN' not in from_clause:  # if everything is done in one table
        query = 'SELECT {} {};'.format(select_clause, from_clause)
        proj.logger.debug('Running {}'.format(query))
        cur.execute(query)
        fldTypes = [None] * len(items)
        for rec in cur:
            for i in range(len(items)):
                if rec[i] is None: # missing
                    continue
                elif fldTypes[i] is None:
                    fldTypes[i] = type(rec[i])
                    continue
                if type(rec[i]) != fldTypes[i]:
                    if type(rec[i]) is float and fldTypes[i] is int:
                        fltType[i] = float
                    else:
                        raise ValueError('Inconsistent type returned from different samples')
            if all([x is not None for x in fldTypes]):
                break
        #
        count = [0]*3
        # if adding a new field
        cur_fields = proj.db.getHeaders(table)[3:]
        for field, fldType in zip([x.split('=', 1)[0] for x in items], fldTypes):
            if field.lower() not in [x.lower() for x in cur_fields]:
                if fldType is None:
                    raise ValueError('Cannot determine the value of a new field {} because the values are all NULL'.format(field))
                proj.checkFieldName(field, exclude=table)
                proj.logger.info('Adding field {}'.format(field))
                query = 'ALTER TABLE {} ADD {} {} NULL;'.format(table, field,
                    {int: 'INT',
                     float: 'FLOAT',
                     str: 'VARCHAR(255)',
                     unicode: 'VARCHAR(255)'}[fldType])
                proj.logger.debug(query)
                cur.execute(query)
                count[1] += 1  # new
            else:
                # FIXME: check the case for type mismatch
                count[2] += 1  # updated
        proj.db.commit()
        # really update things
        query = 'UPDATE {} SET {};'.format(table, ','.join(items))
        proj.logger.debug('Running {}'.format(query))
        cur.execute(query)
    else:
        query = 'SELECT {}, {}.variant_id {};'.format(select_clause, table, from_clause)
        proj.logger.debug('Running {}'.format(query))
        cur.execute(query)
        fldTypes = [None] * len(items)
        s = delayedAction(proj.logger.info, 'Evaluating all expressions')
        results = cur.fetchall()
        del s
        #
        for res in results:
            for i in range(len(items)):
                if res[i] is None: # missing
                    continue
                elif fldTypes[i] is None:
                    fldTypes[i] = type(res[i])
                    continue
                if type(res[i]) != fldTypes[i]:
                    if type(res[i]) is float and fldTypes[i] is int:
                        fltType[i] = float
                    else:
                        raise ValueError('Inconsistent type returned from different samples')
            if all([x is not None for x in fldTypes]):
                break
        #
        count = [0]*3
        # if adding a new field
        cur_fields = proj.db.getHeaders(table)[3:]
        new_fields = [x.split('=', 1)[0] for x in items]
        for field, fldType in zip(new_fields, fldTypes):
            if field.lower() not in [x.lower() for x in cur_fields]:
                if fldType is None:
                    raise ValueError('Cannot determine the value of a new field {} because the values are all NULL'.format(field))
                proj.checkFieldName(field, exclude=table)
                proj.logger.info('Adding field {}'.format(field))
                query = 'ALTER TABLE {} ADD {} {} NULL;'.format(table, field,
                    {int: 'INT',
                     float: 'FLOAT',
                     str: 'VARCHAR(255)',
                     unicode: 'VARCHAR(255)'}[fldType])
                proj.logger.debug(query)
                cur.execute(query)
                count[1] += 1  # new
            else:
                # FIXME: check the case for type mismatch
                count[2] += 1  # updated
        proj.db.commit()
        # really update things
        query = 'UPDATE {} SET {} WHERE variant_id={};'.format(table,
            ','.join(['{}={}'.format(x, proj.db.PH) for x in new_fields]), proj.db.PH)
        proj.logger.debug('Using query {}'.format(query))
        prog = ProgressBar('Updating {}'.format(table), len(results))
        for count, res in enumerate(results):
            cur.execute(query, res)
            if count % 10000 == 0:
                prog.update(count)
        prog.done()


def calcSampleStat(proj, from_stat, IDs, variant_table, genotypes):
    '''Count sample allele count etc for specified sample and variant table'''
    if not proj.isVariantTable(variant_table):
        raise ValueError('"Variant_table {} does not exist.'.format(variant_table))
    #
    #
    # NOTE: this function could be implemented using one or more query more
    # or less in the form of
    #
    # UPDATE variant SET something = something 
    # FROM 
    # (SELECT variant_id, avg(FIELD) FROM (
    #       SELECT FIELD FROM genotype_1 WHERE ...
    #       UNION SELECT FIELD FROM genotype_2 WHERE ...
    #       ...
    #       UNION SELECT FIELD FROM genotype_2 WHERE ) as total
    #   GROUP BY variant_id;
    #
    # This query can be faster because it is executed at a lower level, we cannot
    # really see the progress of the query though.
    #
    if not from_stat:
        proj.logger.warning('No statistics is specified')
        return

    # separate special functions...
    num = hom = het = other = cnt = None

    # keys to speed up some operations
    MEAN = 0
    SUM = 1
    MIN = 2
    MAX = 3
    operationKeys = {'avg': MEAN, 'sum': SUM, 'min': MIN, 'max': MAX}
    possibleOperations = operationKeys.keys()
    
    operations = []
    genotypeFields = []
    validGenotypeFields = []
    destinations = []
    fieldCalcs = []
    for stat in from_stat:
        f, e = [x.strip() for x in stat.split('=')]
        if e == '#(alt)':
            num = f
        elif e == '#(hom)':
            hom = f
        elif e == '#(het)':
            het = f
        elif e == '#(other)':
            other = f
        elif e == '#(GT)':
            cnt = f
        elif e.startswith('#('):
            raise ValueError('Unrecognized parameter {}: only parameters alt, hom, het, other and GT are accepted for special function #'.format(stat))
        else:
            m = re.match('(\w+)\s*=\s*(avg|sum|max|min)\s*\(\s*(\w+)\s*\)\s*', stat)
            if m is None:
                raise ValueError('Unrecognized parameter {}, which should have the form of FIELD=FUNC(GENO_INFO) where FUNC is one of #, avg, sum, max and min'.format(stat))
            dest, operation, field = m.groups()
            if operation not in possibleOperations:
                raise ValueError('Unsupported operation {}.  Supported operations include {}.'.format(operation, ', '.join(possibleOperations)))
            operations.append(operationKeys[operation])
            genotypeFields.append(field)
            fieldCalcs.append(None)
            destinations.append(dest)
    #
    coreDestinations = [num, hom, het, other, cnt]
    cur = proj.db.cursor()
    if IDs is None:
        cur.execute('SELECT sample_id from sample;')
        IDs = [x[0] for x in cur.fetchall()]
    #
    numSample = len(IDs)
    if numSample == 0:
        proj.logger.warning('No sample is selected.')
        return
    
    # Error checking with the user specified genotype fields
    # 1) if a field does not exist within one of the sample genotype tables a warning is issued
    # 2) if a field does not exist in any sample, it is not included in validGenotypeFields
    # 3) if no fields are valid and no core stats were requested (i.e., num, het, hom, other), then sample_stat is exited
    genotypeFieldTypes = {}
    fieldInTable = defaultdict(list)
    for id in IDs:
        fields = [x.lower() for x in proj.db.getHeaders('{}_genotype.genotype_{}'.format(proj.name, id))]
        for field in fields:
            fieldInTable[field].append(id)
            if field not in genotypeFieldTypes:
                genotypeFieldTypes[field] = 'INT'
                fieldType = proj.db.typeOfColumn('{}_genotype.genotype_{}'.format(proj.name, id), field) 
                if fieldType.upper().startswith('FLOAT'):
                    genotypeFieldTypes[field] = 'FLOAT'
                elif fieldType.upper().startswith('VARCHAR'):
                    genotypeFieldTypes[field] = 'VARCHAR'
                    # We had been throwing an error here if a genotype field is a VARCHAR, but I think we should allow
                    # VARCHAR fields in the genotype tables.  We'll throw an error if someone wants to perform numeric operations on these fields
                    # further down in the code.
                    # raise ValueError('Genotype field {} is a VARCHAR which is not supported with sample_stat operations.'.format(field))

    validGenotypeIndices = []
    for index, field in enumerate(genotypeFields):
        if field.lower() not in [x.lower() for x in genotypeFieldTypes.keys()]:
            proj.logger.warning("Field {} is not an existing genotype field within your samples: {}".format(field, str(genotypeFieldTypes.keys())))
        else:
            if len(fieldInTable[field.lower()]) < len(IDs):
                proj.logger.warning('Field {} exists in {} of {} selected samples'.format(field, len(fieldInTable[field.lower()]), len(IDs))) 
            validGenotypeIndices.append(index)
            validGenotypeFields.append(field)
    # check GT field
    if not all([x is None for x in coreDestinations]):
        if 'gt' not in [x.lower() for x in genotypeFieldTypes.keys()]:
            proj.logger.warning('Genotype field does not exist in any of the selected samples')
        else:
            if len(fieldInTable['gt']) < len(IDs):
                proj.logger.warning('Genotype field GT exists in {} of {} selected samples'.format(len(fieldInTable[field.lower()]), len(IDs))) 

    if all([x is None for x in coreDestinations]) and len(validGenotypeFields) == 0:
        proj.logger.warning("No valid sample statistics operation has been specified.")
        return
    
    queryDestinations = coreDestinations
    for index in validGenotypeIndices:
        queryDestinations.append(destinations[index])
    for name in queryDestinations:
        if name is not None:
            proj.checkFieldName(name, exclude=variant_table)
    #
    variants = dict()
    prog = ProgressBar('Counting variants', len(IDs))
    prog_step = max(len(IDs) // 100, 1) 
    for id_idx, id in enumerate(IDs):
        where_cond = []
        if genotypes is not None and len(genotypes) != 0:
            where_cond.extend(genotypes)
        if variant_table != 'variant':
            where_cond.append('variant_id in (SELECT variant_id FROM {})'.format(variant_table))
        whereClause = 'WHERE ' + ' AND '.join(['({})'.format(x) for x in where_cond]) if where_cond else ''
        
        fieldSelect = ['GT' if ('gt' in fieldInTable and id in fieldInTable['gt']) else 'NULL']
        if validGenotypeFields is not None and len(validGenotypeFields) != 0:
            fieldSelect.extend([x if id in fieldInTable[x.lower()] else 'NULL' for x in validGenotypeFields])
        
        if not fieldSelect or all([x == 'NULL' for x in fieldSelect]):
            continue

        query = 'SELECT variant_id {} FROM {}_genotype.genotype_{} {};'.format(' '.join([',' + x for x in fieldSelect]),
            proj.name, id, whereClause)
        #proj.logger.debug(query)
        cur.execute(query)

        for rec in cur:
            if rec[0] not in variants:
                variants[rec[0]] = [0, 0, 0, 0]
                variants[rec[0]].extend(list(fieldCalcs))

            # type heterozygote
            if rec[1] is not None:
                variants[rec[0]][3] += 1
            if rec[1] == 1:
                variants[rec[0]][0] += 1
            # type homozygote
            elif rec[1] == 2:
                variants[rec[0]][1] += 1
            # type double heterozygote with two different alternative alleles
            elif rec[1] == -1:
                variants[rec[0]][2] += 1
            elif rec[1] not in [0, None]:
                proj.logger.warning('Invalid genotype type {}'.format(rec[1]))
        
            # this collects genotype_field information
            if len(validGenotypeFields) > 0:
                for index in validGenotypeIndices:
                    queryIndex = index + 2     # to move beyond the variant_id and GT fields in the select statement
                    recIndex = index + 4       # first 4 attributes of variants are het, hom, double_het and wildtype
                    # ignore missing (NULL) values, and empty string that, if so inserted, could be returned
                    # by sqlite even when the field type is INT.
                    if rec[queryIndex] in [None, '']:
                        continue
                    operation = operations[index]
                    field = genotypeFields[index]
                    if operation == MEAN:
                        if variants[rec[0]][recIndex] is None:
                            # we need to track the number of valid records
                            variants[rec[0]][recIndex] = [rec[queryIndex], 1]
                        else:
                            variants[rec[0]][recIndex][0] += rec[queryIndex]
                            variants[rec[0]][recIndex][1] += 1
                    elif operation == SUM:
                        if variants[rec[0]][recIndex] is None:
                            variants[rec[0]][recIndex] = rec[queryIndex]
                        else:
                            variants[rec[0]][recIndex] += rec[queryIndex]
                    elif operation == MIN:
                        if variants[rec[0]][recIndex] is None or rec[queryIndex] < variants[rec[0]][recIndex]:
                            variants[rec[0]][recIndex] = rec[queryIndex]
                    elif operation == MAX:
                        if variants[rec[0]][recIndex] is None or rec[queryIndex] > variants[rec[0]][recIndex]:
                            variants[rec[0]][recIndex] = rec[queryIndex]  
        if id_idx % prog_step == 0:
            prog.update(id_idx + 1)
    prog.done()
    if len(variants) == 0:
        raise ValueError('No variant is updated')
    #
    headers = [x.lower() for x in proj.db.getHeaders(variant_table)]
    table_attributes = [(num, 'INT'), (hom, 'INT'),
            (het, 'INT'), (other, 'INT'), (cnt, 'INT')]
    fieldsDefaultZero = [num, hom, het, other, cnt]
    
    for index in validGenotypeIndices:
        field = genotypeFields[index]
        genotypeFieldType = genotypeFieldTypes.get(genotypeFields[index]) 
        
        if genotypeFieldType == 'VARCHAR':
            raise ValueError('Genotype field {} is a VARCHAR which is not supported with sample_stat operations.'.format(field))
        
        if operations[index] == MEAN:
            table_attributes.append((destinations[index], 'FLOAT'))
        else:                
            table_attributes.append((destinations[index], genotypeFieldType))
    for field, fldtype in table_attributes:
        if field is None:
            continue
        # We are setting default values on the count fields to 0.  The genotype stat fields are set to NULL by default.
        defaultValue = 0 if field in fieldsDefaultZero else None
        if field.lower() in headers:
            if proj.db.typeOfColumn(variant_table, field) != (fldtype + ' NULL'):
                proj.logger.warning('Type mismatch (existing: {}, new: {}) for column {}. Please remove this column and recalculate statistics if needed.'\
                    .format(proj.db.typeOfColumn(variant_table, field), fldtype, field))
            proj.logger.info('Resetting values at existing field {}'.format(field))
            proj.db.execute('Update {} SET {} = {};'.format(variant_table, field, proj.db.PH), (defaultValue, ))
        else:
            proj.logger.info('Adding field {}'.format(field))
            proj.db.execute('ALTER TABLE {} ADD {} {} NULL;'.format(variant_table, field, fldtype))
            if defaultValue == 0:
                proj.db.execute ('UPDATE {} SET {} = 0'.format(variant_table, field))              
    #
    prog = ProgressBar('Updating {}'.format(variant_table), len(variants))
    update_query = 'UPDATE {0} SET {2} WHERE variant_id={1};'.format(variant_table, proj.db.PH,
        ' ,'.join(['{}={}'.format(x, proj.db.PH) for x in queryDestinations if x is not None]))
    warning = False
    for count,id in enumerate(variants):
        value = variants[id]
        res = []
        if num is not None:
            # het + hom * 2 + other 
            res.append(value[0] + value[1] * 2 + value[2])
        if hom is not None:
            res.append(value[1])
        if het is not None:
            res.append(value[0])
        if other is not None:
            res.append(value[2])
        if cnt is not None:
            res.append(value[3])
            
        # for genotype_field operations, the value[operation_index] holds the result of the operation
        # except for the "mean" operation which needs to be divided by num_samples that have that variant
        try:
            for index in validGenotypeIndices:
                operationIndex = index + 4     # the first 4 indices hold the values for hom, het, double het and total genotype
                operationCalculation = value[operationIndex]
                if operations[index] == MEAN and operationCalculation is not None:
                    res.append(float(operationCalculation[0]) / operationCalculation[1])
                else:
                    res.append(operationCalculation)
            cur.execute(update_query, res + [id])
        except Exception as e:
            proj.logger.debug(e)
        if count % proj.db.batch == 0:
            proj.db.commit()
            prog.update(count)
    proj.db.commit()
    prog.done()
    proj.logger.info('{} records are updated'.format(count))

def updateArguments(parser):
    parser.add_argument('table', help='''variants to be updated.''')
    files = parser.add_argument_group('Update from files')
    files.add_argument('--from_file', nargs='+',
        help='''A list of files that will be used to add or update existing fields of
            variants. The file should be delimiter separated with format described by
            parameter --format. Gzipped files are acceptable. If input files contains
            genotype information, have been inputted before, and can be linked to the
            samples they created without ambiguity (e.g. single sample, or samples with
            detectable sample names), genotypes and their information will also be
            updated.''')
    files.add_argument('--build',
        help='''Build version of the reference genome (e.g. hg18) of the input files,
            which should be the primary (used by default) or alternative (if available)
            reference genome of the project. An alternative reference genome will be
            added to the project if needed.''')
    files.add_argument('--format',
        help='''Format of the input text file. It can be one of the variant tools
            supported file types such as ANNOVAR_output (cf. 'vtools show formats'),
            or a local format specification file (with extension .fmt). Some formats 
            accept parameters (cf. 'vtools show format FMT') and allow you to update
            additional or alternative fields from the input file.''')
    files.add_argument('-j', '--jobs', metavar='N', default=1, type=int,
        help='''Number of processes to import input file. Variant tools by default
            uses a single process for reading and writing, and can use one or more
            dedicated reader processes (jobs=2 or more) to process input files. Due
            to the overhead of inter-process communication, more jobs do not
            automatically lead to better performance.''')
    field = parser.add_argument_group('Set value from existing fields')
    field.add_argument('--set', metavar='EXPR', nargs='*', default=[],
        help='''Add a new field or updating an existing field using a constant
            (e.g. mark=1) or an expression using other fields (e.g. freq=num/120,
            refgene=refGene.name). If multiple values are returned for a variant, only
            one of them will be used. Parameter samples could be used to limit the
            affected variants.''')
    #field.add_argument('-s', '--samples', nargs='*', metavar='COND', default=[],
    #    help='''Limiting variants from samples that match conditions that
    #        use columns shown in command 'vtools show sample' (e.g. 'aff=1',
    #        'filename like "MG%%"').''')
    #field.add_argument('--build',
    #    help='''Reference genome to use when chr and pos is used in expression.''')
    stat = parser.add_argument_group('Set fields from sample statistics')
    stat.add_argument('--from_stat', metavar='EXPR', nargs='*', default=[],
        help='''One or more expressions such as meanQT=avg(QT) that aggregate genotype info (e.g. QT)
            of variants in all or selected samples to specified fields (e.g. meanQT). Functions sum, avg,
            max, and min are currently supported. In addition, special functions #(GT), #(alt), #(hom),
            #(het) and  #(other) are provided to count the number of valid genotypes (not NULL),
            alternative alleles, homozygotes, heterozygotes, and individuals with two different
            alterantive alleles.''')
    stat.add_argument('-s', '--samples', nargs='*', metavar='COND', default=[],
        help='''Limiting variants from samples that match conditions that
            use columns shown in command 'vtools show sample' (e.g. 'aff=1',
            'filename like "MG%%"').''')
    stat.add_argument('--genotypes', nargs='*', metavar='COND', default=[],
        help='''Limiting variants from samples that match conditions that
            use columns shown in command 'vtools show genotypes' (e.g. 'GQ>15').''')


def update(args):
    try:
        with Project(verbosity=args.verbosity) as proj:
            if not args.from_file and not args.from_stat and not args.set:
                proj.logger.warning('Please specify one of --from_file, --from_set and --from_stat for command vtools upate')
            if args.from_file: 
                proj.db.attach(proj.name + '_genotype')
                importer = TextUpdater(proj=proj, table=args.table, files=args.from_file,
                    build=args.build, format=args.format, jobs=args.jobs, fmt_args=args.unknown_args)
                importer.importData()
                # no need to finalize
            if args.set:
                for item in args.set:
                    try:
                        field, expr = [x.strip() for x in item.split('=', 1)]
                    except Exception as e:
                        raise ValueError('Invalid parameter {}, which should have format field=expr_of_field: {}'.format(item, e))
                setFieldValue(proj, args.table, args.set, proj.build)
                #, ' AND '.join(['({})'.format(x) for x in args.samples]))
            if args.from_stat:
                proj.db.attach(proj.name + '_genotype')
                variant_table = args.table if args.table else 'variant'
                if not proj.db.hasTable(variant_table):
                    raise ValueError('Variant table {} does not exist'.format(variant_table))
                IDs = None
                if args.samples:
                    IDs = proj.selectSampleByPhenotype(' AND '.join(['({})'.format(x) for x in args.samples]))
                    if len(IDs) == 0:
                        proj.logger.info('No sample is selected (or available)')
                        return
                    else:
                        proj.logger.info('{} samples are selected'.format(len(IDs)))
                calcSampleStat(proj, args.from_stat, IDs, variant_table, args.genotypes)
        proj.close()
    except Exception as e:
        sys.exit(e)

