#!/usr/bin/env python
# encoding: utf-8
"""
comparebillingreports.py

Created by Anne Pajon on 2013-10-04.
"""

import sys
import os
from collections import defaultdict
import argparse

def main():
    # get the options
    parser = argparse.ArgumentParser()
    parser.add_argument("--last-report", dest="report1", action="store", help="path to last billing report '/path/to/billing/report/201401-billing.csv'", required=True)
    parser.add_argument("--this-report", dest="report2", action="store", help="path to this billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    options = parser.parse_args()
    
    data1 = create_report_from_file(options.report1)
    data2 = create_report_from_file(options.report2)
    
    print "--------------------------------------------------------------------------------"
    print "-- lanes in %s NOT FOUND in %s" % (options.report1, options.report2)
    print "--------------------------------------------------------------------------------"
    for key, value in data1.iteritems():
        if not key in data2.keys():
            print key
            
    print "--------------------------------------------------------------------------------"
    print "-- lanes in %s DO NOT MATCH in %s" % (options.report1, options.report2)
    print "--------------------------------------------------------------------------------"
    for key, value in data1.iteritems():
        if key in data2.keys():
            if not value == data2[key]:
                print '---'
                print value
                print data2[key]

    print "================================================================================"
    new_flowcells = defaultdict(list)
    all_flowcells = defaultdict(list)
    print "--------------------------------------------------------------------------------"
    print "-- ***WARNING*** more than one entry found in %s for these flow-cells" % (options.report2)
    print "--------------------------------------------------------------------------------"
    for key, value in data2.iteritems():
        content = value[0].split(';')
        if len(value) > 1:
            print key, value
        all_flowcells[content[3]].append("%s_%s" % (key, content[0]))
        if not key in data1.keys():
            new_flowcells[content[3]].append("%s_%s" % (key, content[0]))

    print "--------------------------------------------------------------------------------"
    print "-- NEW flow-cells in %s NOT FOUND in %s" % (options.report2, options.report1)
    print "--------------------------------------------------------------------------------"
    for fc, value in new_flowcells.iteritems():
        print fc, value
"""
    print "================================================================================"
    wrong_fc = defaultdict(list)
    print "--------------------------------------------------------------------------------"
    print "-- WRONG number of lanes in flow-cells in %s" % (options.report2)
    print "--------------------------------------------------------------------------------"
    for fc, value in all_flowcells.iteritems():
        if fc.startswith('000000000') or fc.startswith('A'):
            if not len(value) == 1:
                wrong_fc[fc] = len(value)
        elif fc.startswith('C') or fc.startswith('D') or fc.startswith('6'):
            if not len(value) == 8:
                wrong_fc[fc] = len(value)
        elif fc.startswith('H'):
            if not len(value) == 2:
                wrong_fc[fc] = len(value)
        else:
            wrong_fc[fc] = len(value)
        
    for fc, value in wrong_fc.iteritems():
        print fc, value
    

    print "--------------------------------------------------------------------------------"
    print "-- lanes in %s NOT FOUND in %s with billing month NOT EQUAL to 2013-12" % (options.report2, options.report1)
    print "--------------------------------------------------------------------------------"
    for key, value in data2.iteritems():
        if not key in data1.keys():
            content = value.split(';')
            if not content[5] == '2013-12':
                print key, value

    print "--------------------------------------------------------------------------------"
    print "-- lanes in %s NOT FOUND in %s with billing month EQUAL to 2013-12" % (options.report2, options.report1)
    print "--------------------------------------------------------------------------------"
    for key, value in data2.iteritems():
        if not key in data1.keys():
            content = value.split(';')
            if content[5] == '2013-12':
                print key, value
"""    
    
def create_report_from_file(file_report):
    # file format
    # "researcher";"lab";"institute";"slxid"***;"runtype"***;"billable"***;"billingmonth";"flowcellid"***;"lane"***;
    data = defaultdict(list)
    with open (file_report, "U") as f:
        for line in f.readlines():
            content = line.strip().replace('"','').split(';')
            if not content[7] in 'flowcellid':
                key = "%s_%s" % (content[7], content[8])
                data[key].append(';'.join(content[3:6] + content[7:9]))
    return data
        


if __name__ == '__main__':
    main()

