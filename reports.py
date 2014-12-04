#!/usr/bin/env python
# encoding: utf-8
"""
reports.py

Created by Anne Pajon on 2014-01-31.
"""
import os
import csv
from collections import defaultdict
import argparse
import string
import locale
import subprocess

locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')

# email modules
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

# email addresses
ANNE = 'anne.pajon@cruk.cam.ac.uk'
JAMES = 'james.hadfield@cruk.cam.ac.uk'
SARAH = 'sarah.leigh-brown@cruk.cam.ac.uk'
KAREN = 'Karen.Martin@cruk.cam.ac.uk'
HELPDESK = 'genomics-helpdesk@cruk.cam.ac.uk'

def pricing_version(pricing_summary_table_file):
    cmd = ["svn", "info", pricing_summary_table_file]
    process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = process.communicate()[0]
    lines = out.split('\n')
    version = 'Version information of pricing filename '
    for line in lines:
        if line.startswith('Name:'):
            version += "'" + line.split()[1] + "': ["
        if line.startswith('Revision:'):
            version += line + '; '
        if line.startswith('Last Changed Date:'):
            version += line + ']'
    return version


def main():
    # get the options
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", dest="report", action="store", help="path to billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    parser.add_argument("--previous-report", dest="previous_report", action="store", help="path to billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    parser.add_argument("--accounts", dest="accounts", action="store", help="path to the list of the group accounts '/path/to/billing/report/201402-account.csv'", required=True)
    parser.add_argument("--prices", dest="prices", action="store", help="path to the pricing summary table '/path/to/PricingSummaryTable.txt'", required=True)
    parser.add_argument("--notifications", dest="notifications", action="store", help="path to the billing notification file '/path/to/BillingNotificationContacts.txt'")
    parser.add_argument("--date", dest="date", action="store", help="date to produce group reports e.g. '2014-01'", required=True)
    parser.add_argument("--outputdir", dest="outputdir", action="store", help="path to the output folder '/path/to/billing/'", required=True)
    parser.add_argument("--email", dest="email", action="store_true", default=False, help="Send email to genomics with monthly billing report and comparison")
    #parser.add_argument("--cumulative", dest="cumulative", action="store_true", default=False, help="Produce a cumulative report till the date entered")
    options = parser.parse_args()
    
    # ----------
    # billing and group report
    data = parse_billing_report(options.report, options.date)
    
    institute_sequencing_by_runtype = defaultdict(lambda: defaultdict(int))
    sequencing_by_runtype = defaultdict(lambda: defaultdict(int))
    all_institutes = set()
    all_groups = set()
    group_hiseq_usage = defaultdict(lambda: defaultdict(int))
    lab_member_hiseq_usage = defaultdict(lambda: defaultdict(int))
    group_miseq_usage = defaultdict(lambda: defaultdict(int))
    lab_member_miseq_usage = defaultdict(lambda: defaultdict(int))
    billing_table_by_institute = defaultdict(str)
    billing_table_by_group = defaultdict(str)
    
    # institute template
    with open(os.path.join(os.path.dirname(__file__), 'js', 'institute-report-template.html'), "r") as f:
        institute_template = f.read()

    # group template
    with open(os.path.join(os.path.dirname(__file__), 'js', 'group-report-template.html'), "r") as f:
        group_template = f.read()
        
    # group accounts
    group_accounts = defaultdict(dict)
    group_external = defaultdict(str)
    group_collaboration = defaultdict(str)
    institute_groups = defaultdict(str)
    with open(options.accounts, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            group_accounts[line['group']] = line['pricing']
            group_external[line['group']] = line['external']
            if line['collaboration'] == 'False':
                group_collaboration[line['group']] = 'N'
            else:
                group_collaboration[line['group']] = 'Y'
            institute_groups[line['group']] = line['institute']

    # prices
    runtype_prices = defaultdict(dict)
    with open(options.prices, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            runtype_prices[line['Run Type']] = {'Total Price': line['Total Price'], 'Consumables Only': line['Consumables Only'], 'Ad hoc (x1.2)': line['Ad hoc (x1.2)'], 'Commercial (x1.5)': line['Commercial (x1.5)']}

    with open(options.prices, "U") as f:
        summary_prices = f.read()

    # billing data
    hiseq_total_yield = 0
    miseq_total_yield = 0
    billing_codes = defaultdict(set)
    for key, value in data.iteritems():
        institute_sequencing_by_runtype[value['runtype']][value['institute']] += 1
        sequencing_by_runtype[value['runtype']][value['lab']] += 1

        price = ''
        if value['billable'] == 'Bill':
            price = runtype_prices[value['runtype']][group_accounts[value['lab']]]
        billing_table_by_institute[value['institute']] += '["%s", "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s", "£%s"],' % (value['lab'], value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'], price)
        billing_table_by_group[value['lab']] += '[ "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s"],' % (value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'])
        
        all_institutes.add(value['institute'])
        all_groups.add(value['lab'])
        if value['runtype'].lower().startswith('hiseq'):
            group_hiseq_usage[value['institute']][value['lab']] += int(value['cycles'])
            lab_member_hiseq_usage[value['lab']][value['researcher']] += int(value['cycles'])
            hiseq_total_yield += value['yield_value']
        elif value['runtype'].lower().startswith('miseq'):
            group_miseq_usage[value['institute']][value['lab']] += int(value['cycles'])
            lab_member_miseq_usage[value['lab']][value['researcher']] += int(value['cycles'])
            miseq_total_yield += value['yield_value']

        if value['billingcode'] and (group_external[value['lab']] == 'False' or group_collaboration[value['lab']] == 'Y'):
            billing_codes[value['lab']].add(value['billingcode'])

    print "================================================================================"
    print "Billing Summary Report for %s" % options.date
    print "================================================================================"
    # ADD full today
    categories = sorted(sequencing_by_runtype.keys())
    total = defaultdict(int)
    total_count = defaultdict(int)
    summary_header = 'institute\tgroup\toutside_collaboration\t'
    for cat in categories:
        summary_header += '%s\t' % cat
    summary_text = summary_header + '\ttotal\tbilling_codes\n'
    summary_text_count = summary_header + '\ttotal\tbilling_codes\n'
    external_hiseq_total_count = 0
    external_miseq_total_count = 0
    for group in group_accounts.keys():
        summary_line = institute_groups[group] + '\t' + group + '\t' + group_collaboration[group] + '\t'
        summary_line_count = institute_groups[group] + '\t' + group + '\t' + group_collaboration[group] + '\t'
        group_total = 0
        group_total_count = 0
        for cat in categories:
            count = sequencing_by_runtype[cat].get(group, 0)
            cost = count * float(runtype_prices[cat][group_accounts[group]])
            summary_line += '£%.2f\t' % cost
            group_total += cost
            total[cat] += cost
            summary_line_count += '%s\t' % count
            group_total_count += count
            total_count[cat] += count
            if group_external[group] == 'True':
                if cat.lower().startswith('hiseq'):
                    external_hiseq_total_count += count
                if cat.lower().startswith('miseq'):
                    external_miseq_total_count += count
        summary_text += summary_line + '\t£%.2f\t[%s]\n' % (group_total, ", ".join(str(e) for e in billing_codes[group]))
        summary_text_count += summary_line_count + '\t%s\t[%s]\n' % (group_total_count, ", ".join(str(e) for e in billing_codes[group]))
    summary_line = 'total\t'
    hiseq_total_spent = 0
    miseq_total_spent = 0
    grand_total_spent = 0
    summary_line_count = 'total\t'
    hiseq_total_count = 0
    miseq_total_count = 0
    for cat in categories:
        summary_line += '£%.2f\t' % total[cat]
        if cat.lower().startswith('hiseq'):
            hiseq_total_spent += total[cat]
            hiseq_total_count += total_count[cat]
        if cat.lower().startswith('miseq'):
            miseq_total_spent += total[cat]
            miseq_total_count += total_count[cat]
        grand_total_spent += total[cat]
        summary_line_count += '%s\t' % total_count[cat]
    grand_total_count = hiseq_total_count + miseq_total_count
    summary_text += summary_line + '\t£%.2f\n' % grand_total_spent
    summary_text_count += summary_line_count + '\t%s\n' % grand_total_count
    print summary_text_count
    print " "
    print summary_text
    print "================================================================================"
    filename = options.date + '-billing-summary.csv'
    filedir = os.path.join(options.outputdir, 'summaries')
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    billing_summary_file = os.path.join(filedir, filename)
    with open(billing_summary_file, 'w') as f: 
        f.write(summary_text_count)
        f.write("\n")
        f.write("\n")
        f.write(summary_text)
        f.write("\n")
        f.write("\n")
        f.write(summary_prices)
        f.write("\n")
        f.write("\n")
        f.write(pricing_version(options.prices))

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
            institute_data.append(institute_value * 100.0 / float(total_value))
            others_data.append(100 - institute_value * 100.0 / float(total_value))
                
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
        with open(os.path.join(filedir, filename), 'w') as f:
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
            group_data.append(group_value * 100.0 / total_value)
            others_data.append(100 - group_value * 100.0 / total_value)
                
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
        with open(os.path.join(filedir, filename), 'w') as f:
            f.write(string.Template(group_template).safe_substitute({'categories': categories, 'group': group, 'date': options.date, 'group_data': group_data, 'others_data': others_data, 'group_capacity': sum(group_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table}))
    
    # ----------
    # billing email report
    
    # parse billing reports
    this_month_data, this_month_non_billable_data = parse_billing_report_for_comparison(options.report)
    last_month_data, last_month_non_billable_data = parse_billing_report_for_comparison(options.previous_report)
    
    # get all new lanes and count billable duplicated ones for this month
    new_lanes = []
    dup_lanes = []
    billable_dup = 0
    billable_not_this_month = 0
    new_lane_number = 0
    for key, value in this_month_data.iteritems():
        if len(value) > 1:
            billable_flag = False
            for v in value:
                content = v.split(';')
                if content[2] == 'Bill' and content[3] == options.date:
                    billable_flag = True
            if billable_flag:
                billable_dup += 1
                dup_lanes.append(value)
        if not key in last_month_data.keys():
            content = value[0].split(';')
            if not content[3] == options.date:
                billable_not_this_month += 1
            new_lane_number += 1
            new_lanes.append(value) 
            
    # non billable data
    hiseq_non_billable = 0
    miseq_non_billable = 0
    non_billable = 0
    non_billable_lanes = []
    for key, value in this_month_non_billable_data.iteritems():
        if not key in last_month_non_billable_data.keys():
            content = value[0].split(';')
            if content[3] == options.date:
                if not content[2]:
                    non_billable_lanes.append(value)
                    non_billable += 1
                else:
                    if content[1].lower().startswith('hiseq'):
                        hiseq_non_billable += 1
                    if content[1].lower().startswith('miseq'):
                        miseq_non_billable += 1
    
    # compare billing reports & create report
    print "================================================================================"
    print "Billing Comparison Report for %s" % options.date
    print "================================================================================"
    comparison_text = "Billing Summary Report for %s\n" % options.date
    comparison_text += "--------------------------------------------------------------------------------\n"
    comparison_text += "THIS MONTH SUMMARY\n"
    comparison_text += "\n"
    comparison_text += "- HiSeq total number of lanes: %s\n" % hiseq_total_count
    comparison_text += "- HiSeq 'Do Not Bill' lanes: %s\n" % hiseq_non_billable
    comparison_text += "- HiSeq external lanes: %s\n" % external_hiseq_total_count
    comparison_text += "- HiSeq total read sum: %s million\n" % locale.format("%.0f", hiseq_total_yield, grouping=True)
    comparison_text += "- HiSeq total charged cost: %s\n" % locale.currency(hiseq_total_spent, grouping=True) 
    comparison_text += "\n"
    comparison_text += "- MiSeq total number of lanes: %s\n" % miseq_total_count
    comparison_text += "- MiSeq 'Do Not Bill' lanes: %s\n" % miseq_non_billable
    comparison_text += "- MiSeq external lanes: %s\n" % external_miseq_total_count
    comparison_text += "- MiSeq total read sum: %s million\n" % locale.format("%.0f", miseq_total_yield, grouping=True)
    comparison_text += "- MiSeq total charged cost: %s\n" % locale.currency(miseq_total_spent, grouping=True) 
    comparison_text += "\n"
    comparison_text += "- Number of lanes without billable status: %s\n" % non_billable
    comparison_text += "\n"
    comparison_text += "- Number of lanes duplicated and billed: %s\n" % billable_dup
    comparison_text += "\n"
    comparison_text += "- Number of new lanes where billing month is not this month: %s\n" % billable_not_this_month
    comparison_text += "\n"
    comparison_text += "- Total charged number of lanes this month: %s\n" % grand_total_count
    comparison_text += "\n"
    comparison_text += "- Total charged value this month: %s\n" % locale.currency(grand_total_spent, grouping=True)
    comparison_text += "\n"    
    comparison_text += "--------------------------------------------------------------------------------\n"
    comparison_text += "COMPARISON WITH LAST MONTH\n"
    comparison_text += "\n"  
    comparison_text += "- Lanes missing since last report: \n"  # key [flowcellid_lane] in last report but not found in this one
    no_lane = True
    for key, value in last_month_data.iteritems():
        if not key in this_month_data.keys():
            no_lane = False
            comparison_text += "%s\n" % key
    if no_lane:
        comparison_text += "none\n"
    comparison_text += "\n"  
    comparison_text += "- Lanes changed since last report: \n"  # key with value ['SLXID;run_type;billing_status;billing_month;flowcellid;lane] in last report which do not match in this one
    no_lane = True
    for key, value in last_month_data.iteritems():
        if key in this_month_data.keys():
            if len(set(value).intersection(this_month_data[key])) == 0:
                no_lane = False
                comparison_text += "---\n"
                comparison_text += "NEW: %s\n" % this_month_data[key]
                comparison_text += "OLD: %s\n" % value
    if no_lane:
        comparison_text += "none\n"
    comparison_text += "\n"  
    comparison_text += "- Lanes duplicated and billed in this report: \n"
    no_lane = True
    i = 0
    for item in dup_lanes:
        no_lane = False
        i += 1
        comparison_text += "%s\t%s\n" % (i, item)
    if no_lane:
        comparison_text += "none\n"
    comparison_text += "\n"  
    comparison_text += "- Lanes without billable status in this report: \n"
    no_lane = True
    i = 0
    for item in non_billable_lanes:
        no_lane = False
        i += 1
        comparison_text += "%s\t%s\n" % (i, item)
    if no_lane:
        comparison_text += "none\n"
    comparison_text += "\n"
    comparison_text += "- Lanes new in this report: \n"    
    new_lane_number = 0
    for item in new_lanes:
        new_lane_number += 1
        comparison_text += "%s\t%s\n" % (new_lane_number, item)
    comparison_text += "--------------------------------------------------------------------------------"
    print comparison_text
    print "================================================================================"
            
    filename = options.date + '-billing-comparison.txt'
    filedir = os.path.join(options.outputdir, 'summaries')
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    comparison_report_file = os.path.join(filedir, filename)
    with open(comparison_report_file, 'w') as f: 
        f.write(comparison_text)
        
    # ----------
    # send report by email
    if options.email:
        send_email(new_lane_number, [options.report, comparison_report_file, billing_summary_file], options.date)

    # ----------
    # Institute billing notification
    if options.notifications:
        institute_contacts = defaultdict(dict)
        with open(options.notifications, "U") as f:
            reader = csv.DictReader(f, delimiter='\t')
            for line in reader:
                institute_contacts[line['institute']] = {'emails': line['emails'], 'names': line['names']}
                filename = options.date + '-' + line['institute'].replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
                filedir = os.path.join(options.outputdir, 'institutes')
                institute_report = os.path.join(filedir, filename)
                if os.path.exists(institute_report):
                    send_notification(line['emails'].split(','), [institute_report], options.date, line['names'], line['institute'])
                    print 'Email sent to', line['institute'], 'with', institute_report
                else:
                    print 'FILE DO NOT EXISTS', institute_report


def parse_billing_report_for_comparison(file_report):
    data = defaultdict(list)
    non_billable_data = defaultdict(list)
    with open(file_report, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            if line['billable'] == 'Bill':
                key = "%s_%s" % (line['flowcellid'], line['lane'])
                data[key].append(';'.join([line['slxid'], line['runtype'], line['billable'], line['billingmonth'], line['flowcellid'], line['lane']]))
            else:
                key = "%s_%s" % (line['flowcellid'], line['lane'])
                non_billable_data[key].append(';'.join([line['slxid'], line['runtype'], line['billable'], line['billingmonth'], line['flowcellid'], line['lane']])) 
    return data, non_billable_data


def send_email(lane_number, files, month):    
    msg = MIMEMultipart()
    send_from = ANNE
    send_to = [ANNE, JAMES, SARAH, KAREN]

    msg['Subject'] = 'Automatic Billing Report Notification - %s' % month
    msg['From'] = ANNE
    msg['To'] = ','.join(send_to)
    msg.attach(MIMEText("""
    There are %s new lanes in this month billing report.
    Please find attached the billing data, the comparison report and the billing summary files.
    
    Billing reports: http://sol-srv004.cri.camres.org/ngsreports/billing/
    Summary reports: http://sol-srv004.cri.camres.org/ngsreports/summaries/
    Group reports: http://sol-srv004.cri.camres.org/ngsreports/groups/
    Institute reports: http://sol-srv004.cri.camres.org/ngsreports/institutes/
    --
    Anne Pajon, CRI Bioinformatics Core
    anne.pajon@cruk.cam.ac.uk | +44 (0)1223 769 631
    """ % lane_number))
    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    s = smtplib.SMTP('smtp.cruk.cam.ac.uk')
    s.sendmail(send_from, send_to, msg.as_string())
    s.quit()


def send_notification(send_to, files, month, names, institute):
    msg = MIMEMultipart()
    send_from = HELPDESK

    msg['Subject'] = 'CRUK-CIGC Automated Billing Report of %s' % month
    msg['From'] = HELPDESK
    msg['To'] = ','.join(send_to)
    msg.attach(MIMEText("""Dear %(names)s,

Attached is the automated billing report of %(month)s from our LIMs showing the lane-by-lane breakdown of the %(institute)s usage of the HiSeq 2500 reagent rental collaboration, and your use of our MiSeq instruments.

You can see which individuals have been using the service, what sort of sequencing they have been doing and what the cost per lane was for each lane processed. This data should be all you require to complete and cross-charging within the %(institute)s.

If there are any issues with this report please quote the SLX-ID of the lanes in question and contact us at genomics-helpdesk@cruk.cam.ac.uk.

Please do contact me if you have any questions about this.
Sincerely,
James.
--
Cambridge Institute Genomics Core (CIGC)
genomics-helpdesk@cruk.cam.ac.uk
    """ % {'names': names, 'month': month, 'institute': institute}))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    mail = smtplib.SMTP('smtp.cruk.cam.ac.uk')
    mail.sendmail(send_from, send_to + [ANNE, SARAH, JAMES], msg.as_string())
    mail.quit()


def parse_billing_report(file_report, month):
    data = defaultdict(dict)
    with open(file_report, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            if line['billable'] == 'Bill' and line['billingmonth'] == month:
                key = "_".join([line['flowcellid'], line['lane'], line['slxid']])
                line['cycles'] = convert_runtype_into_cycles(line['runtype'].split('_'))
                if line['yield']:
                    line['yield'] = '%.0f' % float(line['yield'])
                    line['yield_value'] = float(line['yield'])
                else:
                    line['yield'] = 'N/A'
                    line['yield_value'] = 0.0
                    print 'no yield for %s' % key
                line['runtype'] = line['runtype'].replace('V3', '').replace('V2', '')
                if line['runtype'].lower().startswith('miseq'):
                    if line['cycles'] <= 150:
                        line['runtype'] = 'MiSeq_UpTo150'
                    else:
                        line['runtype'] = 'MiSeq_UpTo600'
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
            return int(runtype[1][2:]) * 2
    elif runtype[0].lower().startswith('qaiix'):
        if runtype[1].startswith('SE'):
            return int(runtype[1][2:])
        elif runtype[1].startswith('PE'):
            return int(runtype[1][2:]) * 2
    else:
        return int(runtype[1])

if __name__ == '__main__':
    main()

