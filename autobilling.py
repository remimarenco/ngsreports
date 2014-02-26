#!/usr/bin/env python
# encoding: utf-8
"""
autobilling.py

Created by Anne Pajon on 2013-10-04.
"""

import sys
import os
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
    print >>output, "--------------------------------------------------------------------------------"
    print >>output, "-- ***WARNING*** more than one entry found in %s for these lanes" % (options.last_month_report)
    print >>output, "--------------------------------------------------------------------------------"
    for key, value in this_month_data.iteritems():
        content = value[0].split(';')
        if len(value) > 1:
            print >>output, key, value
        if not key in last_month_data.keys():
            new_lanes[content[3]].append(value) 

    print >>output, "--------------------------------------------------------------------------------"
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
        send_email(i, [options.last_month_report, options.output])

def parse_billing_report(file_report, with_extra=False):
    # file format
    # 0:"researcher";1:"lab";2:"institute";3:"slxid"***;4:"runtype"***;5:"billable"***;6:"billingmonth";7:"flowcellid"***;8:"lane"***;
    
    # 0researcher;1lab;2institute;3slxid;4runtype;5billable;6billingmonth;7flowcellid;8lane;9flowcellbillingcomments;10billingcomments;11runfolder;12instrument;13submissiondate;14completiondate;
    data = defaultdict(list)
    with open (file_report, "U") as f:
        for line in f.readlines():
            content = line.strip().replace('"','').split(';')
            if not content[7] in 'flowcellid':
                key = "%s_%s" % (content[7], content[8])
                data[key].append(';'.join(content[3:7] + content[7:9]))
                if with_extra:
                    if content[13] == '':
                        print 'NODATE: %s:%s' % (key, ';'.join(content[3:7] + content[7:9]))
                    else:
                        print '  date: %s:%s' % (key, ';'.join(content[3:7] + content[7:9]))
    return data
    
def send_email(lane_number, files):    
    msg = MIMEMultipart()
    #send_to = [ANNE, JAMES, SARAH]
    send_to = [ANNE]

    msg['Subject'] = 'Automatic Billing Report Notification'
    msg['From'] = ANNE
    msg['To'] = ','.join(send_to)
    msg.attach( MIMEText("""
    There are %s new lanes in this month billing report.
    Please find attached the billing report and its comparison with last month one.
    All billing reports can be found here: http://uk-cri-lsol03.crnet.org:8080/solexa/home/mib-cri/solexa/ngsreports/billing/
    
    Group reports are available too: http://uk-cri-lsol03.crnet.org:8080/solexa//home/mib-cri/solexa/ngsreports/groups/
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
    s.sendmail(me, send_to, msg.as_string())
    s.quit()

        
if __name__ == '__main__':
    main()

