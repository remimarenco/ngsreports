#!/usr/bin/env python
# encoding: utf-8
"""
group_reports.py

Created by Anne Pajon on 2014-01-31.
"""
import sys
import os
import csv
from collections import defaultdict
import argparse
import string

def main():
    # get the options
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", dest="report", action="store", help="path to billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    parser.add_argument("--date", dest="date", action="store", help="date to produce group reports e.g. '2014-01'", required=True)
    parser.add_argument("--outputdir", dest="outputdir", action="store", help="path to the output folder '/path/to/billing/'", required=True)
    parser.add_argument("--cumulative", dest="cumulative", action="store_true", default=False, help="Produce a cumulative report till the date entered")
    options = parser.parse_args()
    
    data = parse_billing_report(options.report, options.date)
    
    institute_sequencing_by_runtype = defaultdict(lambda : defaultdict(int))
    sequencing_by_runtype = defaultdict(lambda : defaultdict(int))
    all_institutes = set()
    all_groups = set()
    group_hiseq_usage = defaultdict(lambda : defaultdict(int))
    lab_member_hiseq_usage = defaultdict(lambda : defaultdict(int))
    group_miseq_usage = defaultdict(lambda : defaultdict(int))
    lab_member_miseq_usage = defaultdict(lambda : defaultdict(int))
    billing_table_by_institute = defaultdict(str)
    billing_table_by_group = defaultdict(str)
    
    # institute template
    with open (os.path.join(os.path.dirname(__file__), 'js', 'institute-report-template.html'), "r") as f:
        institute_template=f.read()

    # group template
    with open (os.path.join(os.path.dirname(__file__), 'js', 'group-report-template.html'), "r") as f:
        group_template=f.read()

    for key, value in data.iteritems():
        institute_sequencing_by_runtype[value['runtype']][value['institute']] += 1
        sequencing_by_runtype[value['runtype']][value['lab']] += 1
        
        billing_table_by_institute[value['institute']] += '["%s", "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s"],' % (value['lab'], value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'])
        billing_table_by_group[value['lab']] += '[ "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s"],' % (value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'])
        
        all_institutes.add(value['institute'])
        all_groups.add(value['lab'])
        if value['runtype'].startswith('Hiseq'):
            group_hiseq_usage[value['institute']][value['lab']] += int(value['cycles'])
            lab_member_hiseq_usage[value['lab']][value['researcher']] += int(value['cycles'])
        elif value['runtype'].startswith('Miseq'):
            group_miseq_usage[value['institute']][value['lab']] += int(value['cycles'])
            lab_member_miseq_usage[value['lab']][value['researcher']] += int(value['cycles'])

    print "================================================================================"
    categories = sorted(sequencing_by_runtype.keys())
    print "categories: %s" % categories
    
    # institute report
    for institute in all_institutes:
        institute_data = []
        others_data = []
        for key in categories:
            institute_value = 0
            if institute in institute_sequencing_by_runtype[key].keys():
                institute_value = institute_sequencing_by_runtype[key][institute]
            others_value = 0
            for other_institute in institute_sequencing_by_runtype[key].keys():
                if not other_institute == institute:
                    others_value += institute_sequencing_by_runtype[key][other_institute]

            total_value = institute_value + others_value
            institute_data.append(institute_value*100.0/float(total_value))
            others_data.append(100 - institute_value*100.0/float(total_value))
                
        hiseq = ''
        for key in group_hiseq_usage[institute].keys():
            hiseq += "['%s', %s]," % (key, group_hiseq_usage[institute][key])

        miseq = ''
        for key in group_miseq_usage[institute].keys():
            miseq += "['%s', %s]," % (key, group_miseq_usage[institute][key])
            
        billing_table = billing_table_by_institute[institute]
        """ 
        { "sTitle": "Group" },
        { "sTitle": "Researcher" },
        { "sTitle": "SLX-ID" },
        { "sTitle": "Run type" },
        { "sTitle": "Flow-cell"},
        { "sTitle": "Lane"},
        { "sTitle": "Yield (M reads)"},
        { "sTitle": "Billable"},
        { "sTitle": "Billing month"}
        """

        filename = options.date + '-' + institute.replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
        print filename
        f = open(os.path.join(options.outputdir, 'institutes', filename),'w')
        f.write(string.Template(institute_template).safe_substitute({'categories': categories, 'institute': institute, 'date': options.date, 'institute_data': institute_data, 'others_data': others_data, 'institute_capacity': sum(institute_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table}))
        f.close()

    # group report
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
            group_data.append(group_value*100.0/total_value)
            others_data.append(100 - group_value*100.0/total_value)
                
        hiseq = ''
        for key in lab_member_hiseq_usage[group].keys():
            hiseq += "['%s', %s]," % (key, lab_member_hiseq_usage[group][key])

        miseq = ''
        for key in lab_member_miseq_usage[group].keys():
            miseq += "['%s', %s]," % (key, lab_member_miseq_usage[group][key])
            
        billing_table = billing_table_by_group[group]
        """ 
        { "sTitle": "Researcher" },
        { "sTitle": "SLX-ID" },
        { "sTitle": "Run type" },
        { "sTitle": "Flow-cell"},
        { "sTitle": "Lane"},
        { "sTitle": "Yield (M reads)"},
        { "sTitle": "Billable"},
        { "sTitle": "Billing month"}
        """
        
        filename = options.date + '-' + group.replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
        print filename
        f = open(os.path.join(options.outputdir, 'groups', filename),'w')
        f.write(string.Template(group_template).safe_substitute({'categories': categories, 'group': group, 'date': options.date, 'group_data': group_data, 'others_data': others_data, 'group_capacity': sum(group_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table}))
        f.close()

def parse_billing_report(file_report, month):
    data = defaultdict(dict)
    with open (file_report, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            if line['billingmonth'] == month:
                key = "_".join([line['flowcellid'], line['lane'], line['slxid']])
                line['cycles'] = convert_runtype_into_cycles(line['runtype'].split('_'))
                if line['yield']:
                    line['yield'] = '%.0f' % float(line['yield'])
                else:
                    line['yield'] = 'N/A'
                    print 'no yield for %s' % key
                line['runtype'] = line['runtype'].replace('V3','').replace('V2','')
                data[key] = line
    return data
        
def convert_runtype_into_cycles(runtype):
    if not runtype[0]:
        return 0
    elif runtype[0] == 'Hiseq':
        if runtype[1].startswith('SE'):
            return int(runtype[1][2:])
        elif runtype[1].startswith('PE'):
            return int(runtype[1][2:])*2
    elif runtype[0] == 'GAIIx':
        if runtype[1].startswith('SE'):
            return int(runtype[1][2:])
        elif runtype[1].startswith('PE'):
            return int(runtype[1][2:])*2
    elif runtype[0] == 'Miseq':
        if runtype[1].endswith('V2') or runtype[1].endswith('V3'):
            return int(runtype[1][:-2])
        else:
            return int(runtype[1])
    else:
        return int(runtype[1])

if __name__ == '__main__':
    main()

