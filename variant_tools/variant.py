#!/usr/bin/env python
#
# $File: variant.py $
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

import sys
from .project import Project
from .utils import ProgressBar, consolidateFieldName, typeOfValues, lineCount
        

def outputArguments(parser):
    parser.add_argument('table', help='''variants to output.''')
    parser.add_argument('fields', nargs='+',
        help='''A list of fields that will be outputed. SQL-compatible expressions
            or functions such as "pos-1", "count(1)" or "sum(num)" are also allowed. ''')

def generalOutputArguments(parser):
    grp = parser.add_argument_group('Output options')
    grp.add_argument('-s', '--save', 
        help='Save output to a file. If unspecified output will be written to the standard output.')
    grp.add_argument('-d', '--delimiter', default='\t',
        help='''Delimiter, default to tab, a popular alternative is ',' for csv output''')
    grp.add_argument('--na', default='NA',
        help='Output string for missing value')
    grp.add_argument('-l', '--limit', default=-1, type=int,
        help='''Number of record to display. Default to all record.''')
    grp.add_argument('--build',
        help='''Output reference genome. If set to alternative build, chr and pos
            in the fields will be replaced by alt_chr and alt_pos''')
    grp.add_argument('-g', '--group_by', nargs='*',
        help='''Group output by fields. This option is useful for aggregation output
            where sumamry statistics are grouped by one or more fields.''')

def outputVariants(proj, table, output_fields, args, query=None, reverse=False):
    '''Output selected fields'''
    # output
    if not args.save:
        out = sys.stdout
    else:
        proj.logger.info('Save output to {}.'.format(args.save))
        out = open(args.save, 'w')
    #
    # table
    if not proj.isVariantTable(table):
        raise ValueError('Variant table {} does not exist.'.format(table))
    #
    # fields
    select_clause, fields = consolidateFieldName(proj, table, ','.join(output_fields))
    #
    # alternative reference genome
    if args.build and args.build == proj.alt_build:
        for idx,item in enumerate(fields):
            if item == 'chr':
                fields[idx] = 'alt_chr'
            if item == 'pos':
                fields[idx] = 'alt_pos'
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
    # WHERE clause
    where_clause = ''
    if query is not None:
        # FIXME: if the query has a simple where clause, we should use that directly.
        where_clause = ' WHERE {}.variant_id {} IN ({})'.format(table, 'NOT' if reverse else '', query)
    # GROUP BY clause
    group_clause = ''
    if args.group_by:
        # is group_by fields outputted?
        tmp, group_fields = consolidateFieldName(proj, table, ','.join(args.group_by))
        for f in group_fields:
            if f.lower() not in [x.lower() for x in fields]:
                raise ValueError('Group attribute {} is not outputted'.format(f))
        group_clause = ' GROUP BY {}'.format(', '.join(group_fields))
    # LIMIT clause
    limit_clause = '' if args.limit < 0 else ' LIMIT 0,{}'.format(args.limit)
    query = 'SELECT {} {} {} {} {};'.format(select_clause, from_clause, where_clause, group_clause, limit_clause)
    proj.logger.debug('Running query {}'.format(query))
    # if output to a file
    cur = proj.db.cursor()
    cur.execute(query)
    proj.logger.info('Writing output')
    prog = ProgressBar(args.save, proj.db.numOfRows(table)) if args.save else None
    for count, rec in enumerate(cur):
        out.write(args.delimiter.join([args.na if x is None else str(x) for x in rec]) + '\n')
        if prog and count % proj.db.batch == 0:
            prog.update(count)
    if prog:
        prog.done()

def output(args):
    try:
        with Project(verbosity=args.verbosity) as proj:
            outputVariants(proj, args.table, args.fields, args)
    except Exception as e:
        sys.exit(e) 

def selectArguments(parser):
    parser.add_argument('from_table', help='''Source variant table.''')
    parser.add_argument('condition', nargs='+',
        help='''Conditions by which variants are selected. Multiple conditions
            should be separated by 'AND' or 'OR'.''')
    parser.add_argument('-t', '--to_table',
        help='''Destination variant table. ''')
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument('-c', '--count', action='store_true',
        help='''Output number of variant, which is a shortcut to '--output count(1)'.''')
    grp.add_argument('-o', '--output', nargs='*', default=[],
        help='''A list of fields that will be outputed. SQL-compatible expressions
            or functions such as "pos-1", "count(1)" or "sum(num)" are also allowed. ''')


def select(args, reverse=False):
    try:
        with Project(verbosity=args.verbosity) as proj:
            # table?
            if not proj.isVariantTable(args.from_table):
                raise ValueError('Variant table {} does not exist.'.format(args.from_table))
            if not args.to_table and not args.output and not args.count:
                proj.logger.warning('Neither --to_table and --output/--count is specified. Nothing to do.')
                return
            # fields? We need to replace things like sift_score to dbNSFP.sift_score
            condition, fields = consolidateFieldName(proj, args.from_table, ' AND '.join(['({})'.format(x) for x in args.condition]))
            # 
            fields_info = sum([proj.linkFieldToTable(x, args.from_table) for x in fields], [])
            # WHERE clause: () is important because OR in condition might go beyond condition
            where_clause = ' WHERE ({})'.format(condition)
            # 
            # FROM clause
            from_clause = 'FROM {} '.format(args.from_table)
            # avoid duplicate
            processed = set()
            for table, conn in [(x.table, x.link) for x in fields_info if x.table != '']:
                if (table.lower(), conn) not in processed:
                    from_clause += ', {} '.format(table)
                    where_clause += ' AND ({}) '.format(conn)
                    processed.add((table.lower(), conn))
            #
            # we are treating different outcomes different, for better performance
            #
            # NOTE: count/output do not co-exist
            #
            # case:       count,  to_table, output
            # 1:           Y       N       N   <- select count(variant)
            # 2:           N       Y       Y   <- generate table, then count and output
            #              Y       Y       N
            #              N       Y       N
            # 3:           N       N       Y   <- direct output
            #
            # Others:      N       N       N   <- do nothing.
            #              Y       Y       Y   <- not allowed
            #              Y       N       Y
            #
            # case 1: simple count.
            if args.count and not args.to_table and not args.output:
                query = 'SELECT count({}.variant_id) {} {};'.format(args.from_table,
                    from_clause, where_clause)
                proj.logger.debug('Running query {}'.format(query))
                proj.db.startProgress('Counting variants')
                cur = proj.db.cursor()
                cur.execute(query)
                count = cur.fetchone()[0]
                # exclude ...
                if reverse:
                    count = proj.db.numOfRows(args.from_table) - int(count)
                proj.db.stopProgress()
                #
                if not args.save:
                    print count
                else:
                    proj.logger.info('Save output to {}'.format(args.save))
                    out = open(args.save, 'w')
                    out.write('{}\n'.format(count))
                    out.close()
            # case 2: to table
            elif args.to_table:
                if proj.db.hasTable(args.to_table):
                    proj.logger.warning('Removing existing table {}, which can be slow for sqlite3 database'.format(args.to_table))
                    proj.db.removeTable(args.to_table)
                #
                proj.createVariantTable(args.to_table)
                if not reverse:
                    query = 'INSERT INTO {0} SELECT {1}.variant_id {2} {3};'.format(args.to_table, args.from_table,
                        from_clause, where_clause)
                else:
                    query = 'INSERT INTO {0} SELECT {1}.variant_id FROM {1} WHERE {1}.variant_id NOT IN (SELECT {1}.variant_id {2} {3});'.\
                        format(args.to_table, args.from_table, from_clause, where_clause)
                proj.logger.debug('Running query {}'.format(query))
                #
                cur = proj.db.cursor()
                proj.db.startProgress('Running')
                cur.execute(query)
                proj.db.stopProgress()
                proj.db.commit()
                #
                count = proj.db.numOfRows(args.to_table)
                proj.logger.info('{} variants selected.'.format(count))
                if args.output:
                    outputVariants(proj, args.to_table, args.output, args)
                if args.count:
                    if not args.save:
                        print count
                    else:
                        proj.logger.info('Save output to {}'.format(args.save))
                        out = open(args.save, 'w')
                        out.write('{}\n'.format(count))
                        out.close()
            # case 3: output, but do not write to table, and not count
            elif args.output: 
                query = 'SELECT {}.variant_id {} {}'.format(args.from_table,
                    from_clause, where_clause)
                outputVariants(proj, args.from_table, args.output, args, query, reverse)
    except Exception as e:
        sys.exit(e) 

def excludeArguments(parser):
    parser.add_argument('from_table', help='''Source variant table.''')
    parser.add_argument('condition', nargs='+',
        help='''Conditions by which matching variants are execluded. Multiple
            conditions should be separated by 'AND' or 'OR'.''')
    parser.add_argument('-t', '--to_table', 
        help='''Destination variant table. Default to a temporary table named''')
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument('-c', '--count', action='store_true',
        help='''Output number of variant, which is a shortcut to '--output count(1)'.''')
    grp.add_argument('-o', '--output', nargs='*', default=[],
        help='''A list of fields that will be outputed. SQL-compatible expressions
            or functions such as "pos-1", "count(1)" or "sum(num)" are also allowed. ''')


def exclude(args):
    select(args, reverse=True)

def compareArguments(parser):
    parser.add_argument('table_A', help='''variant table A.''')
    parser.add_argument('table_B', help='''variant table B.''')
    parser.add_argument('--A_diff_B',  
        help='''Save variants in A but not in B to a table''')
    parser.add_argument('--B_diff_A',  
        help='''Save variants in B but not in A to a table''')
    parser.add_argument('--A_and_B',  
        help='''Save variants in both tables A and B.''')
    parser.add_argument('--A_or_B',  
        help='''Save variants in both tables A or B.''')
    parser.add_argument('-c', '--count', action='store_true',
        help='''Output number of variant that are only in A, only in B, in both A and B, and in A or B.''')

def compare(args):
    try:
        with Project(verbosity=args.verbosity) as proj:
            # table?
            if not proj.isVariantTable(args.table_A):
                raise ValueError('Variant table {} does not exist.'.format(args.table_A))
            if not proj.isVariantTable(args.table_B):
                raise ValueError('Variant table {} does not exist.'.format(args.table_B))
            if not args.A_diff_B and not args.B_diff_A and not args.A_and_B and not args.A_or_B and not args.count:
                proj.logger.warning('No action parameter is specified. Nothing to do.')
                return
            #
            cur = proj.db.cursor()
            # read variants in table_A
            proj.logger.info('Reading {:,} variants in {}...'.format(proj.db.numOfRows(args.table_A), args.table_A))
            cur.execute('SELECT variant_id from {};'.format(args.table_A))
            variant_A = set([x[0] for x in cur.fetchall()])
            # read variants in table_B
            proj.logger.info('Reading {:,} variants in {}...'.format(proj.db.numOfRows(args.table_B), args.table_B))
            cur.execute('SELECT variant_id from {};'.format(args.table_B))
            variant_B = set([x[0] for x in cur.fetchall()])
            #
            # output?
            if args.count:
                print '{}\t{}\t{}\t{}'.format(len(variant_A - variant_B), 
                    len(variant_B - variant_A),
                    len(variant_A & variant_B),
                    len(variant_A | variant_B)
                    )
            #
            for var, table in [
                    (set() if args.A_diff_B is None else variant_A - variant_B, args.A_diff_B), 
                    (set() if args.B_diff_A is None else variant_B - variant_A, args.B_diff_A), 
                    (set() if args.A_and_B is None else variant_A & variant_B, args.A_and_B), 
                    (set() if args.A_or_B is None else variant_A | variant_B, args.A_or_B)]:
                if table is None:
                    continue
                if table == 'variant':
                    raise ValueError('Cannot overwrite master variant table')
                if proj.db.hasTable(table):
                    proj.logger.warning('Removing existing table {}, which can be slow for sqlite3 database'.format(table))
                    proj.db.removeTable(table)
                proj.createVariantTable(table)
                prog = ProgressBar('Writing to ' + table, len(var))
                query = 'INSERT INTO {} VALUES ({});'.format(table, proj.db.PH)
                # sort var so that variant_id will be in order, which might
                # improve database performance
                for count,id in enumerate(sorted(var)):
                    cur.execute(query, (id,))
                    if count % proj.db.batch == 0:
                        proj.db.commit()
                        prog.update(count)
                proj.db.commit()
                prog.done()
    except Exception as e:
        sys.exit(e) 


def addColumnArguments(parser):
    parser.add_argument('table', help='''variant table to which the properties will be attached.''')
    parser.add_argument('fields', nargs='+',
        help='''Column names that will be added to the variant table''')
    parser.add_argument('-f', '--file', required=True,
        help='''A file from which properties will be read.''')
    parser.add_argument('-c', '--columns', required=True, nargs='+', type=int,
        help='Columns (1-based) to import, corresponding to each field to import.')
    grp = parser.add_argument_group('Input file description')
    grp.add_argument('--variant_columns', nargs='+', type=int,
        help='''Columns to hold chr, pos and alt, default to 1, 2 and 4. If a list
            of two columns are given, they are assumed to be chr and pos.''')
    grp.add_argument('--build', 
        help='Reference genome used in specified file. Must be either the primary or alternative build of the project.')
    grp.add_argument('-z', '--zero', action='store_true',
        help='Whether or not specified file uses zero-based index. If unspecified, pos is assumed to be 1-based.')
    grp.add_argument('-d', '--delimiter', default='\t',
        help='''Delimiter, default to tab, a popular alternative is ',' for csv output''')
    grp.add_argument('--na', default='NA',
        help='Treat values matching this value as missing.')


def addColumn(args):
    try:
        with Project(verbosity=args.verbosity) as proj:
            # table?
            if not proj.isVariantTable(args.table):
                raise ValueError('Table {} does not exist or is not a variant table.'.format(args.table))
            # field?
            for f in args.fields:
                proj.checkFieldName(f, exclude=args.table)
            if len(args.fields) != len(args.columns):
                raise ValueError('Number of columns ({}) does not match number of fields ({})'\
                    .format(len(args.columns), len(args.fields)))
            # build?
            if args.build is None or args.build == proj.build:
                build = proj.build
            elif args.build == proj.alt_build:
                build = proj.alt_build
            else:
                raise ValueError('Specified reference genome must be the primary or alternative reference genome of the project.')
            # getting variants from table
            if len(args.variant_columns) == 2:
                chr_col = args.variant_columns[0] - 1
                pos_col = args.variant_columns[1] - 1
                alt_col = None
                if args.table == 'variant':
                    if build == proj.build:
                        query = 'SELECT variant_id, chr, pos FROM variant;'
                    else:
                        query = 'SELECT variant_id, alt_chr, alt_pos FROM variant;'
                else:
                    if build == proj.build:
                        query = 'SELECT {0}.variant_id, variant.chr, variant.pos FROM {0} \
                            LEFT OUTER JOIN variant ON {0}.variant_id = variant.variant_id;'.format(args.table)
                    else:
                        query = 'SELECT {0}.variant_id, variant.alt_chr, variant.alt_pos FROM {0} \
                            LEFT OUTER JOIN variant ON {0}.variant_id = variant.variant_id;'.format(args.table)
            elif len(args.variant_columns) == 3:
                chr_col = args.variant_columns[0] - 1
                pos_col = args.variant_columns[1] - 1
                alt_col = args.variant_columns[2] - 1
                if args.table == 'variant':
                    if build == proj.build:
                        query = 'SELECT variant_id, chr, pos, alt FROM variant;'
                    else:
                        query = 'SELECT variant_id, alt_chr, alt_pos, alt FROM variant;'
                else:
                    if build == proj.build:
                        query = 'SELECT {0}.variant_id, variant.chr, variant.pos, variant.alt FROM {0} \
                            LEFT OUTER JOIN variant ON {0}.variant_id = variant.variant_id;'.format(args.table)
                    else:
                        query = 'SELECT {0}.variant_id, variant.alt_chr, variant.alt_pos, variant.alt FROM {0} \
                            LEFT OUTER JOIN variant ON {0}.variant_id = variant.variant_id;'.format(args.table)
            else:
                raise ValueError('Specified file must have either chr, pos or chr, pos and alt fields.\
                    You can check the log file for a list of records.')
            # columns?
            cols = [x - 1 for x in args.columns]
            # getting existing variants
            prog = ProgressBar('Getting variants from {}'.format(args.table), proj.db.numOfRows(args.table))
            cur = proj.db.cursor()
            cur.execute(query)
            variants = {}
            for count, rec in enumerate(cur):
                if alt_col is None:
                    # items with the same chr,pos will be numbered by an index
                    idx = 0
                    while True:
                        if (rec[1], rec[2], idx) not in variants:
                            variants[(rec[1], rec[2], idx)] = [None] * len(args.fields) + [rec[0]]
                            break
                        else:
                            idx += 1
                else:
                    variants[(rec[1], rec[2], rec[3])] = [None] * len(args.fields) + [rec[0]]
                if count % proj.db.batch == 0:
                    prog.update(count)
            prog.done()
            # now read file and update variants table.
            prog = ProgressBar('Reading {}'.format(args.file), lineCount(args.file))
            err_count = 0
            rec_count = 0
            first_ten = 0  # report some record, for debugging purposes
            with open(args.file) as input:
                for count, line in enumerate(input.readlines()):
                    tokens = [x.strip() for x in line.split(args.delimiter)]
                    # get anchor fields
                    try:
                        chr = tokens[chr_col]
                        if chr.startswith('chr'):
                            chr = chr[3:]
                        pos = int(tokens[pos_col])
                        if args.zero:
                            pos += 1
                        # record into the variant table
                        if alt_col is None:
                            if first_ten < 10:
                                proj.logger.debug('{}\t{}\t{}'.format(chr, pos, 
                                    [tokens[c] if tokens[c] != args.na else None for c in cols]))
                                first_ten += 1
                            if (chr, pos, 0) in variants:
                                vals = [tokens[c] if tokens[c] != args.na else None for c in cols]
                                idx = 0
                                while True:
                                    try:
                                        variants[(chr, pos, idx)][:-1] = vals
                                        rec_count += 1
                                        idx += 1
                                    except:
                                        break
                        else:
                            if first_ten < 10:
                                proj.logger.debug('{}\t{}\t{}\t{}'.format(chr, pos, tokens[alt_col],
                                    [tokens[c] if tokens[c] != args.na else None for c in cols]))
                                first_ten += 1
                            if (chr, pos, tokens[alt_col]) in variants:
                                vals = [tokens[c] if tokens[c] != args.na else None for c in cols]
                                variants[(chr, pos, tokens[alt_col])][:-1] = vals
                                rec_count += 1
                    except Exception as e:
                        err_count += 1
                        proj.logger.debug(e)
                        proj.logger.debug(line.rstrip())
                    #
                    if count % proj.db.batch == 0:
                        prog.update(count)
                prog.done()
            proj.logger.info('{} lines processed, {} recorded updated, {} lines ignored due to error'.format(count + 1, rec_count, err_count))
            #
            if rec_count == 0:
                proj.logger.warning('Nothing to update. Perhaps you have specified wrong chr, pos and alt columns?')
                return
            # adding columns:
            headers = proj.db.getHeaders(args.table)
            for idx, field in enumerate(args.fields):
                if field in headers:
                    # NOTE: there is a possible problem of type mismatch 
                    # e.g. saving frequency to an integer column
                    proj.logger.info('Updating existing column {}'.format(field))
                    proj.logger.warning('Result might be wrong if this column was created to hold other types of values')
                else:
                    proj.logger.info('Adding column {}'.format(field))
                    proj.db.execute('ALTER TABLE {} ADD {} {} NULL;'.format(args.table, field, 
                        typeOfValues([x[idx] for x in variants.values() if x[idx] is not None])))
            #
            # updating variants
            prog = ProgressBar('Updating table {}'.format(args.table), len(variants))
            query = 'UPDATE {} SET {} WHERE variant_id = {}'.format(
                args.table, ','.join(['{}={}'.format(f, proj.db.PH) for f in args.fields]), proj.db.PH)
            for count, rec in enumerate(variants.values()):
                if not all([x is None for x in rec[:-1]]):
                    cur.execute(query, rec)
                if count % proj.db.batch == 0:
                    proj.db.commit()
                    prog.update(count)
            proj.db.commit()
            prog.done()
    except Exception as e:
        sys.exit(e) 


