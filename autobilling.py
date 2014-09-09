#!/usr/bin/env python
# encoding: utf-8
"""
autobilling.py

Created by Anne Pajon on 2013-10-04.
"""

import sys
import os
import csv
from collections import defaultdict
import argparse

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

def main():
    # get the options
    parser = argparse.ArgumentParser()
    parser.add_argument("--last-month-report", dest="last_month_report", action="store", help="path to last billing report '/path/to/billing/report/201401-billing.csv'", required=True)
    parser.add_argument("--this-month-report", dest="this_month_report", action="store", help="path to this billing report '/path/to/billing/report/201402-billing.csv'", required=True)
    parser.add_argument("--output", dest="output", action="store", help="path to the output comparison report '/path/to/billing/report/201402-compare-reports-2.out'", required=True)
    parser.add_argument("--email", dest="email", action="store_true", default=False, help="Send email to genomics with monthly billing report and comparison")
    options = parser.parse_args()
    
    # parse billing reports
    this_month_data = parse_billing_report(options.this_month_report)
    last_month_data = parse_billing_report(options.last_month_report)
    
    # compare billing reports & create report
    output = open(options.output, "w")
    print >>output, "================================================================================"
    print >>output, "LAST MONTH REPORT vs THIS MONTH REPORT"
    print >>output, "--------------------------------------------------------------------------------"
    print >>output, "-- key [flowcellid_lane] in LAST %s NOT FOUND in THIS %s" % (options.last_month_report, options.this_month_report)
    print >>output, "--------------------------------------------------------------------------------"
    for key, value in last_month_data.iteritems():
        if not key in this_month_data.keys():
            print >>output, key
            
    print >>output, "--------------------------------------------------------------------------------"
    print >>output, "-- for key with value ['SLXID;run_type;billing_status;billing_month;flowcellid;lane]" 
    print >>output, "-- in LAST %s DO NOT MATCH in THIS %s" % (options.last_month_report, options.this_month_report)
    print >>output, "--------------------------------------------------------------------------------"
    for key, value in last_month_data.iteritems():
        if key in this_month_data.keys():
            if len(set(value).intersection(this_month_data[key])) == 0:
                print >>output, '---'
                print >>output, 'LAST: %s' % value
                print >>output, 'THIS: %s' % this_month_data[key]

    print >>output, "================================================================================"
    print >>output, "THIS REPORT %s" % options.this_month_report
    new_lanes = defaultdict(list)
    print >>output, "********************************************************************************"
    print >>output, "** WARNING *********************************************************************" 
    print >>output, "** more than one entry found in %s for these lanes which are billable" % (options.last_month_report)
    print >>output, "********************************************************************************"
    i=0
    for key, value in this_month_data.iteritems():
        if len(value) > 1:
            billable_flag=False
            for v in value:
                content = v.split(';')
                if content[2] == 'Bill':
                    billable_flag=True
            if billable_flag:
                i += 1
                print >>output, "**", i, ":",  key, value
        if not key in last_month_data.keys():
            content = value[0].split(';')
            new_lanes[content[3]].append(value) 

    print >>output, "********************************************************************************"
    print >>output, "--------------------------------------------------------------------------------"
    print >>output, "-- NEW lanes to be billed this month"
    print >>output, "-- NEW lanes in %s NOT FOUND in %s to bill this month" % (options.this_month_report, options.last_month_report)
    print >>output, "--------------------------------------------------------------------------------"
    i = 0
    for fc, value in new_lanes.iteritems():
        for item in value:
            i += 1
            print >>output, i, item
            
    output.close()
    
    # send report by email
    if options.email:
        send_email(i, [options.this_month_report, options.output])

def parse_billing_report(file_report):
    data = defaultdict(list)
    with open (file_report, "U") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for line in reader:
            if line['billable'] == 'Bill':
                key = "%s_%s" % (line['flowcellid'], line['lane'])
                data[key].append(';'.join([line['slxid'], line['runtype'], line['billable'], line['billingmonth'], line['flowcellid'], line['lane']]))
    return data
    
def send_email(lane_number, files):    
    msg = MIMEMultipart()
    send_from = ANNE
    send_to = [ANNE, JAMES, SARAH, KAREN]
    #send_to = [ANNE]

    msg['Subject'] = 'Automatic Billing Report Notification'
    msg['From'] = ANNE
    msg['To'] = ','.join(send_to)
    msg.attach( MIMEText("""
    There are %s new lanes in this month billing report.
    Please find attached the billing report and its comparison with the one from last month.
    All billing reports can be found here: http://uk-cri-lsol03.crnet.org:8080/solexa/home/mib-cri/solexa/ngsreports/billing/
    
    Summary reports: http://uk-cri-lsol03.crnet.org:8080/solexa/home/mib-cri/solexa/ngsreports/summaries/
    Group reports: http://uk-cri-lsol03.crnet.org:8080/solexa//home/mib-cri/solexa/ngsreports/groups/
    Institute reports: http://uk-cri-lsol03.crnet.org:8080/solexa//home/mib-cri/solexa/ngsreports/institutes/
    --
    Anne Pajon, CRI Bioinformatics Core
    anne.pajon@cruk.cam.ac.uk | +44 (0)1223 769 631
    """ % lane_number))
    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    s = smtplib.SMTP('localhost')
    s.sendmail(send_from, send_to, msg.as_string())
    s.quit()

        
if __name__ == '__main__':
    main()

