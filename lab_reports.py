#!/usr/bin/env python
# encoding: utf-8
"""
lab_reports.py

Created by Anne Pajon on 2014-01-31.
Copyright (c) 2014 __MyCompanyName__. All rights reserved.
"""
import sys
import os
from collections import defaultdict
import argparse

def main():
    # get the options
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", dest="report", action="store", help="path to billing report '/path/to/billing/report/billingreport_Apr2Jan.csv'", required=True)
    options = parser.parse_args()
    
    data = create_report_from_file(options.report)
    
    sequencing_by_runtype = defaultdict(lambda : defaultdict(list))
    lab_member_usage = defaultdict(lambda : defaultdict(list))
    total_capacity = defaultdict(int)
    for key, value in data.iteritems():
        contents = value.split(';')
        sequencing_by_runtype[contents[4]][contents[1]].append(key)
        lab_member_usage[contents[1]][contents[0]].append(key)
        total_capacity[contents[4]] += 1

    for key, value in sequencing_by_runtype.iteritems():
        print "--------------------------------------------------------------------------------"
        print key
        print "--------------------------------------------------------------------------------"
        for i,j in value.iteritems():
            print "\t%s\t%s" % (i, j)

    print "================================================================================"

    for key, value in lab_member_usage.iteritems():
        print "--------------------------------------------------------------------------------"
        print key
        print "--------------------------------------------------------------------------------"
        # TODO: calculate number of cycles
        for i,j in value.iteritems():
            print "\t%s\t%s" % (i, j)

    print "================================================================================"
        
    print total_capacity.items()
    
def create_report_from_file(file_report):
    # file format
    # "researcher***";"lab***";"institute***";"slxid"***;"runtype"***;"billable";"billingmonth";"flowcellid"***;"lane"***;
    data = defaultdict(list)
    with open (file_report, "U") as f:
        for line in f.readlines():
            content = line.strip().replace('"','').split(';')
            if not content[7] in 'flowcellid':
                key = "%s_%s_%s" % (content[7], content[8], content[3])
                data[key] = ';'.join(content[0:5] + content[7:9])
    return data
        


if __name__ == '__main__':
    main()

