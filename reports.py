#!/usr/bin/env python
# encoding: utf-8
"""
reports.py

Created by Anne Pajon on 2014-01-31.
"""
from __future__ import division
import os
import csv
from collections import defaultdict
import argparse
import string
import locale
import subprocess

locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')

# logging
import log as logger
# Templating
from mako.template import Template

# email modules
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

# smtp server
CRUKCI_SMTP = 'smtp.cruk.cam.ac.uk'

# email addresses
ANNE = 'Anne.Pajon@cruk.cam.ac.uk'
JAMES = 'James.Hadfield@cruk.cam.ac.uk'
FATIMAH = 'Fatimah.Bowater@cruk.cam.ac.uk'
KAREN = 'Karen.Martin@cruk.cam.ac.uk'
ANNIE = 'Annie.Baxter@cruk.cam.ac.uk'
HELPDESK = 'genomics-helpdesk@cruk.cam.ac.uk'

# pricing file names
SEQ_SUMMARY_TABLE = 'PricingSummaryTable.txt'
LPS_SUMMARY_TABLE = 'LPSPricingSummaryTable.txt'


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
    # Options:
    #   - report
    #   - previous_report
    #   - lpsreport
    #   - accounts
    #   - prices
    #   - notifications
    #   - date
    #   - outputdir
    #   - email
    #   - logfile
    #   - nologemail
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", dest="report", help="path to sequencing billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    parser.add_argument("--previous-report", dest="previous_report", help="path to last month sequencing billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    parser.add_argument("--lpsreport", dest="lpsreport", help="path to library prep billing report '/path/to/billing/report/201402-lps-billing.csv'")
    parser.add_argument("--accounts", dest="accounts", help="path to the list of the group accounts '/path/to/billing/report/201402-account.csv'", required=True)
    parser.add_argument("--prices", dest="prices", help="path to the pricing summary tables '/path/to/pricing'", required=True)
    parser.add_argument("--notifications", dest="notifications", help="path to the billing notification file '/path/to/BillingNotificationContacts.txt'")
    parser.add_argument("--date", dest="date", help="date to produce group reports e.g. '2014-01'", required=True)
    parser.add_argument("--outputdir", dest="outputdir", help="path to the output folder '/path/to/billing/'", required=True)
    parser.add_argument("--email", dest="email", action="store_true", default=False, help="Send email to genomics with monthly billing report and comparison")
    parser.add_argument("--logfile", dest="logfile", default=None, help="File to print logging information")
    parser.add_argument("--nologemail", dest="nologemail", action="store_true", default=False, help="turn off sending log emails on error")

    options = parser.parse_args()

    # logging configuration
    log = logger.get_custom_logger(options.logfile, options.nologemail)

    # ----------
    # billing and group report
    data, cumulative_data = parse_billing_report(options.report, options.date)

    # ----------
    # institute template
    with open(os.path.join(os.path.dirname(__file__), 'js', 'institute-report-template.html'), "r") as f:
        institute_template = f.read()

    # ----------
    # group template
    with open(os.path.join(os.path.dirname(__file__), 'js', 'group-report-template.html'), "r") as f:
        group_template = f.read()

    # ----------
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

    # ----------
    # sequencing prices
    runtype_prices = defaultdict(dict)
    with open(os.path.join(options.prices, SEQ_SUMMARY_TABLE), "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            runtype_prices[line['Run Type']] = {'Total Price': line['Total Price'], 'Consumables Only': line['Consumables Only'], 'Ad hoc (x1.5)': line['Ad hoc (x1.5)'], 'Commercial (x1.5)': line['Commercial (x1.5)']}

    with open(os.path.join(options.prices, SEQ_SUMMARY_TABLE), "U") as f:
        summary_prices = f.read()

    # library preparation prices
    lps_prices = defaultdict(dict)
    with open(os.path.join(options.prices, LPS_SUMMARY_TABLE), "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            lps_prices[line['Type']] = {'Total Price': line['Total Price'], 'Consumables Only': line['Consumables Only'], 'Ad hoc (x1.5)': line['Ad hoc (x1.5)'], 'Commercial (x1.5)': line['Commercial (x1.5)']}

    # TODO: Merge this with the previous loop to avoid parsing two times the same file
    # First way to do it => Add each line to lps_summary_prices
    with open(os.path.join(options.prices, LPS_SUMMARY_TABLE), "U") as f:
        lps_summary_prices = f.read()

    # ----------
    # billing summary report
    # institute data
    # TODO: Use a Billing object to fill its properties with the parameters (__init__?)
    institute_sequencing_by_runtype, all_institutes, group_hiseq_usage, group_miseq_usage, billing_table_by_institute = transform_data(data, runtype_prices, group_accounts, group_type='institute')
    # lab data
    sequencing_by_runtype, all_groups, lab_member_hiseq_usage, lab_member_miseq_usage, billing_table_by_group = transform_data(data, runtype_prices, group_accounts, group_type='lab')

    # ----------
    # cumulative institute billing summary report
    cumulative_institute_sequencing_by_runtype, cumulative_all_institutes, cumulative_group_hiseq_usage, cumulative_group_miseq_usage, cumulative_billing_table_by_institute = transform_data(cumulative_data, runtype_prices, group_accounts, group_type='institute')


    hiseq_total_yield = 0
    miseq_total_yield = 0
    billing_codes = defaultdict(set)

    for key, value in data.iteritems():
        if value['runtype'].lower().startswith('hiseq'):
            hiseq_total_yield += value['yield_value']
        elif value['runtype'].lower().startswith('miseq'):
            miseq_total_yield += value['yield_value']
        if value['billingcode'] and (group_external[value['lab']] == 'False' or group_collaboration[value['lab']] == 'Y'):
            billing_codes[value['lab']].add(value['billingcode'])

    log.info("================================================================================")
    log.info("Billing Summary Report for %s" % options.date)
    log.info("================================================================================")
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
    summary_line = 'total\t\t\t'
    hiseq_total_spent = 0
    miseq_total_spent = 0
    grand_total_spent = 0
    summary_line_count = 'total\t\t\t'
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
    log.info(summary_text_count)
    log.info(" ")
    log.info(summary_text)
    log.info("================================================================================")
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
        f.write(pricing_version(os.path.join(options.prices, SEQ_SUMMARY_TABLE)))

    # ----------
    # library prep billing summary report
    lps_data, lps_data_groupby_project = parse_lps_billing_report(options.lpsreport, options.date)
    # table for institute/group reports
    lps_billing_table_by_institute = defaultdict(str)
    lps_billing_table_by_group = defaultdict(str)
    for v in lps_data_groupby_project.values():
        lps_billing_table_by_institute[v[0]['institute']] += '["%s", "%s", "%s", "%s", "%s", "%s", "£%.2f", "£%.2f"], ' % (v[0]['lab'], v[0]['researcher'], v[0]['slxid'], len(v), v[0]['lpsbillable'], v[0]['billingmonth'], float(lps_prices[v[0]['lpsbillable']][group_accounts[v[0]['lab']]]), len(v)*float(lps_prices[v[0]['lpsbillable']][group_accounts[v[0]['lab']]]))
        lps_billing_table_by_group[v[0]['lab']] += '["%s", "%s", "%s", "%s", "%s", "£%.2f", "£%.2f"], ' % (v[0]['researcher'], v[0]['slxid'], len(v), v[0]['lpsbillable'], v[0]['billingmonth'], float(lps_prices[v[0]['lpsbillable']][group_accounts[v[0]['lab']]]), len(v)*float(lps_prices[v[0]['lpsbillable']][group_accounts[v[0]['lab']]]))

    lps_categories = sorted(lps_prices.keys())
    log.info("================================================================================")
    log.info("Library Prep Billing Summary Report for %s" % options.date)
    log.info("================================================================================")
    summary_header = 'institute\tgroup\toutside_collaboration'
    for cat in lps_categories:
        summary_header += '\t%s' % cat
    summary_header += '\ttotal\tbilling_codes\n'
    summary_text = summary_header
    summary_text_count = summary_header
    total_count = defaultdict(int)
    total_spent = defaultdict(int)
    for group in group_accounts.keys():
        count = defaultdict(int)
        cost = defaultdict(int)
        billing_codes = set()
        for v in lps_data.values():
            if group == v['lab']:
                billing_codes.add(v['billingcode'])
                for cat in lps_categories:
                    if cat == v['lpsbillable']:
                        count[cat] += 1
                        price = float(lps_prices[v['lpsbillable']][group_accounts[group]])
                        cost[cat] += price

        count_text = ''
        cost_text = ''
        lps_grand_total_count = 0
        lps_grand_total_spent = 0
        for cat in lps_categories:
            count_text += '\t%s' % count[cat]
            cost_text += '\t£%.2f' % cost[cat]
            total_count[cat] += count[cat]
            total_spent[cat] += cost[cat]
            lps_grand_total_count += count[cat]
            lps_grand_total_spent += cost[cat]
        summary_text_count += '%s\t%s\t%s%s\t%s\t[%s]\n' % (institute_groups[group], group, group_collaboration[group], count_text, lps_grand_total_count, ", ".join(str(e) for e in billing_codes))
        summary_text += '%s\t%s\t%s%s\t£%.2f\t[%s]\n' % (institute_groups[group], group, group_collaboration[group], cost_text, lps_grand_total_spent, ", ".join(str(e) for e in billing_codes))
    lps_grand_total_count = 0
    lps_grand_total_spent = 0
    summary_text_count += 'total\t\t'
    summary_text += 'total\t\t'
    for cat in lps_categories:
        summary_text_count += '\t%s' % total_count[cat]
        summary_text += '\t£%.2f' % total_spent[cat]
        lps_grand_total_count += total_count[cat]
        lps_grand_total_spent += total_spent[cat]
    summary_text_count += '\t%s\n' % lps_grand_total_count
    summary_text += '\t£%.2f\n' % lps_grand_total_spent
    log.info(summary_text_count)
    log.info(" ")
    log.info(summary_text)
    log.info("================================================================================")
    filename = options.date + '-lps-billing-summary.csv'
    lps_billing_summary_file = os.path.join(filedir, filename)
    with open(lps_billing_summary_file, 'w') as f:
        f.write(summary_text_count)
        f.write("\n")
        f.write("\n")
        f.write(summary_text)
        f.write("\n")
        f.write("\n")
        f.write(lps_summary_prices)
        f.write("\n")
        f.write("\n")
        f.write(pricing_version(os.path.join(options.prices, LPS_SUMMARY_TABLE)))

    # ----------
    # finance cumulative report
    filename = options.date + '-billing-finance.csv'
    billing_finance_file = os.path.join(filedir, filename)
    with open(billing_finance_file, 'w') as f:
        field_names = ['researcher', 'lab', 'institute', 'slxid', 'runtype', 'billable', 'billingmonth', 'billingcode', 'flowcellid', 'lane', 'yield', 'yield_value', 'cycles', 'external', 'collaboration', 'cost']
        writer = csv.DictWriter(f, fieldnames=field_names, delimiter='\t')
        writer.writeheader()
        for k in cumulative_data.keys():
            cumulative_data[k]['cost'] = '£%.2f' % float(runtype_prices[cumulative_data[k]['runtype']][group_accounts[cumulative_data[k]['lab']]])
            if group_external[cumulative_data[k]['lab']] == 'True':
                cumulative_data[k]['external'] = 'Y'
            else:
                cumulative_data[k]['external'] = 'N'
            cumulative_data[k]['collaboration'] = group_collaboration[cumulative_data[k]['lab']]
            if group_collaboration[cumulative_data[k]['lab']] == 'Y':
                cumulative_data[k]['billingcode'] = cumulative_data[k]['institute']
            writer.writerow(cumulative_data[k])
        f.write("\n")
        f.write("\n")
        f.write(pricing_version(os.path.join(options.prices, SEQ_SUMMARY_TABLE)))
        f.write("\n")
        f.write("\n")
        f.write(summary_prices)

    # ----------
    # library prep finance cumulative report
    filename = options.date + '-lps-billing-finance.csv'
    lps_billing_finance_file = os.path.join(filedir, filename)
    with open(lps_billing_finance_file, 'w') as f:
        field_names = ['researcher', 'lab', 'institute', 'slxid', 'lpsbillable', 'billingmonth', 'billingcode', 'projectname', 'sampleid', 'samplename', 'external', 'collaboration', 'cost']
        writer = csv.DictWriter(f, fieldnames=field_names, delimiter='\t')
        writer.writeheader()
        for k in lps_data.keys():
            lps_data[k]['cost'] = '£%.2f' % float(lps_prices[lps_data[k]['lpsbillable']][group_accounts[lps_data[k]['lab']]])
            if group_external[lps_data[k]['lab']] == 'True':
                lps_data[k]['external'] = 'Y'
            else:
                lps_data[k]['external'] = 'N'
            lps_data[k]['collaboration'] = group_collaboration[lps_data[k]['lab']]
            if group_collaboration[lps_data[k]['lab']] == 'Y':
                lps_data[k]['billingcode'] = lps_data[k]['institute']
            writer.writerow(lps_data[k])
        f.write("\n")
        f.write("\n")
        f.write(pricing_version(os.path.join(options.prices, LPS_SUMMARY_TABLE)))
        f.write("\n")
        f.write("\n")
        f.write(lps_summary_prices)

    # ----------
    # institute report
    create_institute_reports(institute_template, options.date, options.outputdir, all_institutes, institute_sequencing_by_runtype, group_hiseq_usage, group_miseq_usage, billing_table_by_institute, lps_billing_table_by_institute, report_type='standard')

    # ----------
    # institute cumulative report
    create_institute_reports(institute_template, options.date, options.outputdir, cumulative_all_institutes, cumulative_institute_sequencing_by_runtype, cumulative_group_hiseq_usage, cumulative_group_miseq_usage, cumulative_billing_table_by_institute, lps_billing_table_by_institute, report_type='cumulative')

    # ----------
    # group report from lab data
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
        lps_billing_table = lps_billing_table_by_group[group]

        filename = options.date + '-' + group.replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
        filedir = os.path.join(options.outputdir, 'groups')
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        with open(os.path.join(filedir, filename), 'w') as f:
            f.write(string.Template(group_template).safe_substitute({'categories': categories, 'group': group, 'date': options.date, 'group_data': group_data, 'others_data': others_data, 'group_capacity': sum(group_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table, 'lps_billing_table': lps_billing_table}))

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
    #TODO: Take a template, create an object which do the processing before include in the template
    mytemplate = Template(
        filename='./template/mako/billing_comparison_report.txt',
        default_filters=['decode.utf8'],
        input_encoding='utf-8',
        output_encoding='utf-8')
    myTemplateWithData = mytemplate.render(
        date=options.date,
        hiseq_total_count=hiseq_total_count,
        hiseq_non_billable=hiseq_non_billable,
        external_hiseq_total_count=external_hiseq_total_count,
        hiseq_total_yield_format=locale.format("%.0f", hiseq_total_yield, grouping=True),
        hiseq_total_spent_currency=locale.currency(hiseq_total_spent, grouping=True),
        miseq_total_count=miseq_total_count,
        miseq_non_billable=miseq_non_billable,
        external_miseq_total_count=external_miseq_total_count,
        miseq_total_yield_formatted=locale.format("%.0f", miseq_total_yield, grouping=True),
        miseq_total_spent_currency=locale.currency(miseq_total_spent, grouping=True),
        non_billable=non_billable,
        billable_dup=billable_dup,
        billable_not_this_month=billable_not_this_month,
        grand_total_count=grand_total_count,
        grand_total_spent_currency=locale.currency(grand_total_spent, grouping=True),
        last_month_data=last_month_data,
        this_month_data=this_month_data,
        dup_lanes=dup_lanes,
        non_billable_lanes=non_billable_lanes,
        new_lanes=new_lanes
    )

    log.info(myTemplateWithData)

    # TODO: Put this in an print function (Better in a Output objects which also manage the content of the emails)
    filename = options.date + '-billing-comparison.txt'
    filedir = os.path.join(options.outputdir, 'summaries')
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    comparison_report_file = os.path.join(filedir, filename)
    with open(comparison_report_file, 'w') as f:
        f.write(myTemplateWithData)

    # ----------
    # send report by email
    if options.email:
        send_email(new_lane_number, [options.report, comparison_report_file, billing_finance_file, billing_summary_file, options.lpsreport, lps_billing_finance_file, lps_billing_summary_file], options.date)

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
                    log.info('Email sent to ' + line['institute'] + ' with ' + institute_report)
                else:
                    log.info('FILE DO NOT EXISTS: ' + institute_report)


def create_institute_reports(institute_template, date, outputdir, all_institutes, institute_sequencing_by_runtype, group_hiseq_usage, group_miseq_usage, billing_table_by_institute, lps_billing_table_by_institute, report_type='cumulative'):
    for institute in all_institutes:
        institute_data = []
        others_data = []
        categories = sorted(institute_sequencing_by_runtype.keys())
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
        lps_billing_table = lps_billing_table_by_institute[institute]

        if report_type == 'cumulative':
            filename = date + '-cumulative-' + institute.replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
            text_date = 'Cumulative report from last April till %s' % date
        else:
            filename = date + '-' + institute.replace('/', '').replace(' ', '').replace('-', '').lower() + '.html'
            text_date = date
        filedir = os.path.join(outputdir, 'institutes')
        if not os.path.exists(filedir):
            os.makedirs(filedir)

        with open(os.path.join(filedir, filename), 'w') as f:
            f.write(string.Template(institute_template).safe_substitute({'categories': categories, 'institute': institute, 'date': text_date, 'institute_data': institute_data, 'others_data': others_data, 'institute_capacity': sum(institute_data), 'others_capacity': sum(others_data), 'hiseq': hiseq, 'miseq': miseq, 'billing_table': billing_table, 'lps_billing_table': lps_billing_table}))


def transform_data(data, runtype_prices, group_accounts, group_type='institute'):
    sequencing_by_runtype = defaultdict(lambda: defaultdict(int))
    groups = set()
    hiseq_usage = defaultdict(lambda: defaultdict(int))
    miseq_usage = defaultdict(lambda: defaultdict(int))
    billing_table = defaultdict(str)

    for key, value in data.iteritems():

        if value['billable'] == 'Bill':
            price = float(runtype_prices[value['runtype']][group_accounts[value['lab']]])
        if group_type == 'institute':
            sequencing_by_runtype[value['runtype']][value['institute']] += 1
            billing_table[value['institute']] += '["%s", "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s", "£%.2f"],' % (value['lab'], value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'], price)
            groups.add(value['institute'])
            if value['runtype'].lower().startswith('hiseq'):
                hiseq_usage[value['institute']][value['lab']] += int(value['cycles'])
            elif value['runtype'].lower().startswith('miseq'):
                miseq_usage[value['institute']][value['lab']] += int(value['cycles'])
        else:
            sequencing_by_runtype[value['runtype']][value['lab']] += 1
            billing_table[value['lab']] += '[ "%s", "%s", "%s", "%s", "%s" , "%s", "%s", "%s", "£%.2f"],' % (value['researcher'], value['slxid'], value['runtype'], value['flowcellid'], value['lane'], value['yield'], value['billable'], value['billingmonth'], price)
            groups.add(value['lab'])
            if value['runtype'].lower().startswith('hiseq'):
                hiseq_usage[value['lab']][value['researcher']] += int(value['cycles'])
            elif value['runtype'].lower().startswith('miseq'):
                miseq_usage[value['lab']][value['researcher']] += int(value['cycles'])

    return sequencing_by_runtype, groups, hiseq_usage, miseq_usage, billing_table


def send_email(lane_number, files, month):
    log = logger.get_custom_logger()
    msg = MIMEMultipart()
    send_from = ANNE
    send_to = [ANNE, JAMES, FATIMAH, KAREN, ANNIE]

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

    mail = smtplib.SMTP(CRUKCI_SMTP)
    out = mail.sendmail(send_from, send_to, msg.as_string())
    if out:
        log.error(out)
    mail.quit()


def send_notification(send_to, files, month, names, institute):
    log = logger.get_custom_logger()
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

    mail = smtplib.SMTP(CRUKCI_SMTP)
    out = mail.sendmail(send_from, send_to + [ANNE, JAMES], msg.as_string())
    if out:
        log.error(out)
    mail.quit()


def parse_billing_report(file_report, month):
    log = logger.get_custom_logger()
    data = defaultdict(dict)
    cumulative_data = defaultdict(dict)
    with open(file_report, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            if line['billable'] == 'Bill':
                key = "_".join([line['flowcellid'], line['lane'], line['slxid']])
                line['cycles'] = convert_runtype_into_cycles(line['runtype'].split('_'))
                if line['yield']:
                    line['yield'] = '%.0f' % float(line['yield'])
                    line['yield_value'] = float(line['yield'])
                else:
                    line['yield'] = 'N/A'
                    line['yield_value'] = 0.0
                    log.warn('no yield for %s' % key)
                line['runtype'] = line['runtype'].replace('V3', '').replace('V2', '')
                if line['runtype'].lower().startswith('miseq'):
                    if line['cycles'] <= 150:
                        line['runtype'] = 'MiSeq_UpTo150'
                    else:
                        line['runtype'] = 'MiSeq_UpTo600'
                if line['runtype'].lower().startswith('nextseq'):
                    if line['cycles'] <= 75:
                        line['runtype'] = 'NextSeq_UpTo75'
                    elif line['cycles'] <= 150:
                        line['runtype'] = 'NextSeq_UpTo150'
                    else:
                        line['runtype'] = 'NextSeq_UpTo300'
                if line['billingmonth'] == month:
                    data[key] = line
                cumulative_data[key] = line
    return data, cumulative_data
        

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


def parse_lps_billing_report(file_report, month):
    data = defaultdict(dict)
    data_groupby_project = defaultdict(list)
    with open(file_report, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            if line['lpsbillable'].startswith('Bill') and line['billingmonth'] == month:
                line['lpsbillable'] = line['lpsbillable'].split(' - ')[1]
                data[line['sampleid']] = line
                data_groupby_project["|".join([line['institute'], line['lab'], line['researcher'], line['lpsbillable'], line['billingmonth'], line['projectname'], line['slxid']])].append(line)
    return data, data_groupby_project


def convert_runtype_into_cycles(runtype):
    if not runtype[0]:
        return 0
    elif runtype[0].lower().startswith('hiseq') or runtype[0].lower().startswith('miseq') or runtype[0].lower().startswith('nextseq'):
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

