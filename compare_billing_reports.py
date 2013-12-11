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
    parser.add_argument("--report1", dest="report1", action="store", help="path to billing report 1 '/path/to/billing/report/billingreport_Apr2Nov.csv'", required=True)
    parser.add_argument("--report2", dest="report2", action="store", help="path to billing report 2 '/path/to/billing/report/billingreport_Apr2Dec.csv'", required=True)
    options = parser.parse_args()
    
    data1 = create_report_from_file(options.report1)
    data2 = create_report_from_file(options.report2)
    
    print "----------"
    print "-- lanes in %s do not match in %s" % (options.report1, options.report2)
    print "----------"
    for key, value in data1.iteritems():
        if not key in data2.keys():
            print key, value

    print "----------"
    print "-- lanes in %s do not match in %s" % (options.report2, options.report1)
    print "----------"
    for key, value in data2.iteritems():
        if not key in data1.keys():
            print key, value
    
    
def create_report_from_file(file_report):
    # file format
    # "researcher";"lab";"institute";"slxid";"runtype";"billable";"billingmonth";"flowcellid";"lane";
    data = defaultdict(list)
    with open (file_report, "U") as f:
        for line in f.readlines():
            content = line.strip().replace('"','').split(';')
            key = "%s_%s" % (content[7], content[8])
            data[key] = line.strip().replace('"','')
    return data
        


if __name__ == '__main__':
    main()

