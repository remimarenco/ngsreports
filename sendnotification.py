#!/usr/bin/env python
# encoding: utf-8
"""
sendmail

Created by Anne Pajon on 2015-03-26.
"""
# email modules
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

# email addresses
ANNE = 'anne.pajon@cruk.cam.ac.uk'
ANNEGMAIL = 'pajanne@gmail.com'
HELPDESK = 'genomics-helpdesk@cruk.cam.ac.uk'

msg = MIMEMultipart()
send_from = HELPDESK
send_to = [ANNE, ANNEGMAIL]
msg['Subject'] = 'Testing Automated Notification'
msg['From'] = HELPDESK
msg['To'] = ','.join(send_to)
msg.attach(MIMEText("""

Testing Automated Notification...

--
Cambridge Institute Genomics Core (CIGC)
genomics-helpdesk@cruk.cam.ac.uk
"""))

#mail = smtplib.SMTP('smtp.cruk.cam.ac.uk')
mail = smtplib.SMTP('mailrelay.cruk.cam.ac.uk')
mail.set_debuglevel(True)
mail.sendmail(send_from, send_to, msg.as_string())
mail.quit()

