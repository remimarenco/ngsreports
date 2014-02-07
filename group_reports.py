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
import string

def main():
    # get the options
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", dest="report", action="store", help="path to billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    parser.add_argument("--date", dest="date", action="store", help="date to produce group reports e.g. '2014-01'", required=True)
    options = parser.parse_args()
    
    data = create_report_from_file(options.report, options.date)
    
    sequencing_by_runtype = defaultdict(lambda : defaultdict(int))
    all_groups = set()
    lab_member_hiseq_usage = defaultdict(lambda : defaultdict(int))
    lab_member_miseq_usage = defaultdict(lambda : defaultdict(int))
    
    with open (os.path.join('js', 'group-report-template.html'), "r") as f:
        template=f.read()

    for key, value in data.iteritems():
        contents = value.split(';')
        sequencing_by_runtype[contents[4]][contents[1]] += 1
        all_groups.add(contents[1])
        if contents[4].startswith('Hiseq'):
            lab_member_hiseq_usage[contents[1]][contents[0]] += 1
        elif contents[4].startswith('Miseq'):
            lab_member_miseq_usage[contents[1]][contents[0]] += 1

    print "================================================================================"
    categories = sorted(sequencing_by_runtype.keys())
    print "categories: %s" % categories
    
    for group in all_groups:
        group_data = []
        others_data = []
        for key in categories:
            group_value = 0
            if group in sequencing_by_runtype[key].keys():
                group_value = sequencing_by_runtype[key][group]
            others_value = 0
            for other_group in sequencing_by_runtype[key].keys():
                if not other_group == group:
                    others_value += sequencing_by_runtype[key][other_group]

            total_value = group_value + others_value
            group_data.append(group_value*100/total_value)
            others_data.append(100 - group_value*100/total_value)
                
        hiseq = ''
        for key in lab_member_hiseq_usage[group].keys():
            hiseq += "['%s', %s]," % (key, lab_member_hiseq_usage[group][key])

        miseq = ''
        for key in lab_member_miseq_usage[group].keys():
            miseq += "['%s', %s]," % (key, lab_member_miseq_usage[group][key])
        filename = options.date + '-' + group.replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
        print filename
        f = open(os.path.join('groups', filename),'w')
        f.write(string.Template(template).safe_substitute({'categories': categories, 'group': group, 'group_data': group_data, 'others_data': others_data, 'group_capacity': sum(group_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq}))
        f.close()

def create_report_from_file(file_report, month):
    # file format
    # "researcher***";"lab***";"institute***";"slxid"***;"runtype"***;"billable";"billingmonth";"flowcellid"***;"lane"***;
    data = defaultdict(list)
    with open (file_report, "U") as f:
        for line in f.readlines():
            content = line.strip().replace('"','').split(';')
            if not content[7] in 'flowcellid':
                if content[6] == month:
                    key = "%s_%s_%s" % (content[7], content[8], content[3])
                    data[key] = ';'.join(content[0:5] + content[7:9])
    return data
        


if __name__ == '__main__':
    main()

