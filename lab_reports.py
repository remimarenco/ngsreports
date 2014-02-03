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

RUNTYPES = {
'Hiseq_SE36': {'cycles': 36}, 
'Hiseq_SE40': {'cycles': 40}, 
'Hiseq_SE50': {'cycles': 50}, 
'Hiseq_SE75': {'cycles': 75}, 
'Hiseq_SE100': {'cycles': 100}, 
'Hiseq_PE75': {'cycles': 150}, 
'Hiseq_PE100': {'cycles': 200}, 
'Miseq_00300': {'cycles': 300}, 
'Miseq_050V2': {'cycles': 50}, 
'Miseq_150V3': {'cycles': 150}, 
'Miseq_300V2': {'cycles': 300}, 
'Miseq_500V2': {'cycles': 500}, 
'Miseq_600V3': {'cycles': 600}
}

def main():
    # get the options
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", dest="report", action="store", help="path to billing report '/path/to/billing/report/billingreport_Apr2Jan.csv'", required=True)
    options = parser.parse_args()
    
    data = create_report_from_file(options.report)
    
    sequencing_by_runtype = defaultdict(lambda : defaultdict(int))
    lab_member_hiseq_usage = defaultdict(lambda : defaultdict(int))
    lab_member_miseq_usage = defaultdict(lambda : defaultdict(int))

    for key, value in data.iteritems():
        contents = value.split(';')
        sequencing_by_runtype[contents[4]][contents[1]] += 1
        if contents[4].startswith('Hiseq'):
            lab_member_hiseq_usage[contents[1]][contents[0]] += 1
        elif contents[4].startswith('Miseq'):
            lab_member_miseq_usage[contents[1]][contents[0]] += 1

    print "================================================================================"
    categories = sorted(sequencing_by_runtype.keys())
    print "categories: %s" % categories
    #print "data: %s" % 

    group_data = []
    others_data = []
    for key in categories:
        group_value = 0
        if 'Jason Carroll' in sequencing_by_runtype[key].keys():
            group_value = sequencing_by_runtype[key]['Jason Carroll']
        others_value = 0
        for group in sequencing_by_runtype[key].keys():
            if not group == 'Jason Carroll':
                others_value += sequencing_by_runtype[key][group]

        total_value = group_value + others_value
        group_data.append(group_value*100/total_value)
        others_data.append(100 - group_value*100/total_value)
    print "group data: %s" % group_data
    print "others data: %s" % others_data
    print "================================================================================"
    print "group data: %s" % sum(group_data)
    print "others data: %s" % sum(others_data)
        
    print "================================================================================"
    for key in lab_member_hiseq_usage['Jason Carroll'].keys():
        print "['%s', %s]," % (key, lab_member_hiseq_usage['Jason Carroll'][key])

    print "================================================================================"

    for key in lab_member_miseq_usage['Jason Carroll'].keys():
        print "['%s', %s]," % (key, lab_member_miseq_usage['Jason Carroll'][key])

    print "================================================================================"
        

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

