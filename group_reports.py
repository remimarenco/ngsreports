#!/usr/bin/env python
# encoding: utf-8
"""
group_reports.py

Created by Anne Pajon on 2014-01-31.
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
    parser.add_argument("--outputdir", dest="outputdir", action="store", help="path to the output folder '/path/to/billing/'", required=True)
    options = parser.parse_args()
    
    data = parse_billing_report(options.report, options.date)
    
    sequencing_by_runtype = defaultdict(lambda : defaultdict(int))
    all_groups = set()
    lab_member_hiseq_usage = defaultdict(lambda : defaultdict(int))
    lab_member_miseq_usage = defaultdict(lambda : defaultdict(int))
    billing_table_by_group = defaultdict(str)
    
    with open (os.path.join(os.path.dirname(__file__), 'js', 'group-report-template.html'), "r") as f:
        template=f.read()

    for key, value in data.iteritems():
        contents = value.split('\t')
        sequencing_by_runtype[contents[4]][contents[1]] += 1
        billing_table_by_group[contents[1]] += '[ "%s", "%s", "%s", "%s", "%s" , "%s"],' % (contents[0], contents[3], contents[4], contents[5], contents[6], contents[8])
        all_groups.add(contents[1])
        if contents[4].startswith('Hiseq'):
            lab_member_hiseq_usage[contents[1]][contents[0]] += int(contents[7])
        elif contents[4].startswith('Miseq'):
            lab_member_miseq_usage[contents[1]][contents[0]] += int(contents[7])

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
            group_data.append(group_value*100.0/total_value)
            others_data.append(100 - group_value*100.0/total_value)
                
        hiseq = ''
        for key in lab_member_hiseq_usage[group].keys():
            hiseq += "['%s', %s]," % (key, lab_member_hiseq_usage[group][key])

        miseq = ''
        for key in lab_member_miseq_usage[group].keys():
            miseq += "['%s', %s]," % (key, lab_member_miseq_usage[group][key])
            
        billing_table = billing_table_by_group[group]
        """    { "sTitle": "Researcher" },
            { "sTitle": "SLX-ID" },
            { "sTitle": "Run type" },
            { "sTitle": "Flow-cell"},
            { "sTitle": "Lane"},
            { "sTitle": "Billing comments"}"""
        
        filename = options.date + '-' + group.replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
        print filename
        f = open(os.path.join(options.outputdir, 'groups', filename),'w')
        f.write(string.Template(template).safe_substitute({'categories': categories, 'group': group, 'group_data': group_data, 'others_data': others_data, 'group_capacity': sum(group_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table}))
        f.close()

def parse_billing_report(file_report, month):
    # file format
    # "researcher***"\t"lab***"\t"institute***"\t"slxid"***\t"runtype"***\t"billable"\t"billingmonth"\t"flowcellid"***\t"lane"***\tflowcellbillingcomments\tbillingcomments***
    # "researcher***"\t"lab***"\t"institute***"\t"slxid"***\t"runtype"***\tbillingmonth"\t"flowcellid"***\t"lane"***\tflowcellbillingcomments\tbillingcomments***\tbillable***"\t
    data = defaultdict(list)
    with open (file_report, "U") as f:
        for line in f.readlines():
            content = line.strip().replace('"','').split('\t')
            if not content[7] in 'flowcellid':
                if content[6] == month:
                    key = "%s_%s_%s" % (content[7], content[8], content[3])
                    runtype = content[4].split('_')
                    cycles = convert_runtype_into_cycles(runtype)
                    data[key] = '\t'.join(content[0:4] + [content[4].replace('V3','')] + content[7:9] + [str(cycles), content[10], content[5]])
    return data
        
def convert_runtype_into_cycles(runtype):
    if runtype[0] == 'Hiseq':
        if runtype[1].startswith('SE'):
            return int(runtype[1][2:])
        elif runtype[1].startswith('PE'):
            return int(runtype[1][2:])*2
    elif runtype[0] == 'Miseq':
        if runtype[1].endswith('V3'):
            return int(runtype[1][:-2])
        else:
            return int(runtype[1])
    else:
        return int(runtype[1])

if __name__ == '__main__':
    main()

