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
    print "================================================================================"
    print "LAST REPORT vs THIS REPORT"
    print "--------------------------------------------------------------------------------"
    print "-- key [flowcellid_lane] in LAST %s NOT FOUND in THIS %s" % (options.report1, options.report2)
    print "--------------------------------------------------------------------------------"
    for key, value in data1.iteritems():
        if not key in data2.keys():
            print key
            
    print "--------------------------------------------------------------------------------"
    print "-- for key with value ['SLXID;run_type;billing_status;flowcellid;lane]" 
    print "-- in LAST %s DO NOT MATCH in THIS %s" % (options.report1, options.report2)
    print "--------------------------------------------------------------------------------"
    for key, value in data1.iteritems():
        if key in data2.keys():
            if not value == data2[key]:
                print '---'
                print 'LAST: %s' % value
                print 'THIS: %s' % data2[key]

    print "================================================================================"
    print "THIS REPORT %s" % options.report2
    new_flowcells = defaultdict(list)
    print "--------------------------------------------------------------------------------"
    print "-- ***WARNING*** more than one entry found in %s for these lanes" % (options.report2)
    print "--------------------------------------------------------------------------------"
    for key, value in data2.iteritems():
        content = value[0].split(';')
        if len(value) > 1:
            print key, value
        if not key in data1.keys():
            new_flowcells[content[3]].append(value) 

    print "--------------------------------------------------------------------------------"
    print "-- NEW lanes in %s NOT FOUND in %s to bill this month" % (options.report2, options.report1)
    print "--------------------------------------------------------------------------------"
    i = 0
    for fc, value in new_flowcells.iteritems():
        for item in value:
            i += 1
            print i, item

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

