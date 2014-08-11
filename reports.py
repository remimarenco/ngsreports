#!/usr/bin/env python
# encoding: utf-8
"""
reports.py

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
    parser.add_argument("--accounts", dest="accounts", action="store", help="path to the list of the group accounts '/path/to/billing/report/201402-account.csv'", required=True)
    parser.add_argument("--prices", dest="prices", action="store", help="path to the pricing summary table '/path/to/PricingSummaryTable.txt'", required=True)
    parser.add_argument("--date", dest="date", action="store", help="date to produce group reports e.g. '2014-01'", required=True)
    parser.add_argument("--outputdir", dest="outputdir", action="store", help="path to the output folder '/path/to/billing/'", required=True)
    #parser.add_argument("--cumulative", dest="cumulative", action="store_true", default=False, help="Produce a cumulative report till the date entered")
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
        institute_template = f.read()

    # group template
    with open (os.path.join(os.path.dirname(__file__), 'js', 'group-report-template.html'), "r") as f:
        group_template = f.read()
        
    # group accounts
    group_accounts = defaultdict(dict)
    with open (options.accounts, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            group_accounts[line['group']] = line['pricing']
                    
    # prices
    runtype_prices = defaultdict(dict)
    with open (options.prices, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            runtype_prices[line['Run Type']] = {'Total Price': line['Total Price'], 'Consumables Only': line['Consumables Only'], 'Ad hoc (x1.2)': line['Ad hoc (x1.2)'], 'Commercial (x1.5)': line['Commercial (x1.5)']}

    for key, value in data.iteritems():
        institute_sequencing_by_runtype[value['runtype']][value['institute']] += 1
        sequencing_by_runtype[value['runtype']][value['lab']] += 1
        
        billing_table_by_institute[value['institute']] += '["%s", "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s"],' % (value['lab'], value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'])
        billing_table_by_group[value['lab']] += '[ "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s"],' % (value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'])
        
        all_institutes.add(value['institute'])
        all_groups.add(value['lab'])
        if value['runtype'].lower().startswith('hiseq'):
            group_hiseq_usage[value['institute']][value['lab']] += int(value['cycles'])
            lab_member_hiseq_usage[value['lab']][value['researcher']] += int(value['cycles'])
        elif value['runtype'].lower().startswith('miseq'):
            group_miseq_usage[value['institute']][value['lab']] += int(value['cycles'])
            lab_member_miseq_usage[value['lab']][value['researcher']] += int(value['cycles'])

    print "================================================================================"
    print "Summary Billing Report for %s" % options.date
    print "================================================================================"
    categories = sorted(sequencing_by_runtype.keys())
    total = defaultdict(int)
    total_count = defaultdict(int)
    summary_header = 'group\t'
    summary_text = ''
    summary_text_count = ''
    for cat in categories:
        summary_header += '%s\t' % cat
    summary_text = summary_header + '\n'
    summary_text_count = summary_header + '\n'
    for group in group_accounts.keys():
        summary_line = group + '\t'
        summary_line_count = group + '\t'
        for cat in categories:
            cost = sequencing_by_runtype[cat].get(group, 0) * float(runtype_prices[cat][group_accounts[group]])
            summary_line += '£%.2f\t' % cost
            total[cat] += cost
            summary_line_count += '%s\t' % sequencing_by_runtype[cat].get(group, 0)
            total_count[cat] += sequencing_by_runtype[cat].get(group, 0)
        summary_text += summary_line + '\n'
        summary_text_count += summary_line_count + '\n'
    summary_line = 'total\t'
    summary_line_count = 'total\t'
    for cat in categories:
        summary_line += '£%.2f\t' % total[cat]
        summary_line_count += '%s\t' % total_count[cat]
    summary_text += summary_line + '\n'
    summary_text_count += summary_line_count + '\n'
    print summary_text_count
    print " "
    print summary_text
    print "================================================================================"
    filename = options.date + '-billing-summary.csv'
    filedir = os.path.join(options.outputdir, 'summaries')
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    with open(os.path.join(filedir, filename), 'w') as f: 
        f.write(summary_text_count)
        f.write("")
        f.write(summary_text)
    
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
        filedir = os.path.join(options.outputdir, 'institutes')
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        with open(os.path.join(filedir, filename),'w') as f:
            f.write(string.Template(institute_template).safe_substitute({'categories': categories, 'institute': institute, 'date': options.date, 'institute_data': institute_data, 'others_data': others_data, 'institute_capacity': sum(institute_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table}))

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
        filedir = os.path.join(options.outputdir, 'groups')
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        with open(os.path.join(filedir, filename),'w') as f:
            f.write(string.Template(group_template).safe_substitute({'categories': categories, 'group': group, 'date': options.date, 'group_data': group_data, 'others_data': others_data, 'group_capacity': sum(group_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table}))

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
    print runtype
    if not runtype[0]:
        return 0
    elif runtype[0].lower().startswith('hiseq') or runtype[0].lower().startswith('miseq'):
        if runtype[1].startswith('SE'):
            return int(runtype[1][2:])
        elif runtype[1].startswith('PE'):
            return int(runtype[1][2:])*2
    elif runtype[0].lower().startswith('qaiix'):
        if runtype[1].startswith('SE'):
            return int(runtype[1][2:])
        elif runtype[1].startswith('PE'):
            return int(runtype[1][2:])*2
    else:
        return int(runtype[1])

if __name__ == '__main__':
    main()
