#!/usr/bin/env python
# encoding: utf-8
"""
comparebillingreports.py

Created by Anne Pajon on 2013-10-04.
Copyright (c) 2013 __MyCompanyName__. All rights reserved.
"""

import sys
import os
from collections import defaultdict

def main():
        
    allfcdetails_report = defaultdict(list)
    handmade_fcids = []
    handmade_statuses = defaultdict(list)
    with open ("james_billingreport_Apr2Aug.txt", "U") as f:
        for line in f.readlines():
            content = line.strip().split('\t')
            #if content[8] in ['Bill.', 'Do not bill']:
            status = "-".join(content[8].split())
            fcid = "%s_Lane%s" % (content[0], content[2])
            fcid_withstatus = "%s_%s" % (fcid, status)
            handmade_fcids.append(fcid_withstatus)
            allfcdetails_report[fcid].append("HANDMADE %s" % line.strip())
            handmade_statuses[status].append(fcid)
                
    fcids = []
    statuses = defaultdict(list)
    with open ("billingreport_Apr2Sep_v9.csv", "U") as f:
        for line in f.readlines():
            content = line.strip().split('|')
            if content[13]:
                status = "-".join(content[13].split()).replace('---run-failed', '')
            else:
                status = 'Unknown'
            fcid = "%s_%s" % (content[8].replace('000000000-', ''), content[9])
            fcid_withstatus = "%s_%s" % (fcid, status)
            fcids.append(fcid_withstatus)
            allfcdetails_report[fcid].append("GLS_SQL  %s" % line.strip())
            statuses[status].append(fcid)
            
    i = 0
    fc_dict = defaultdict(list)
    for fcid in fcids:
        if not fcid in handmade_fcids:
            i += 1
            #print ">>> %s no match in handmade report" % fcid
            #print allfcdetails_report[fcid]
            fc_dict[fcid.split('_')[0]].append(fcid)

    print "----------"
    print "-- %s lanes found in billing query do not match in handmade report" % i
    print "----------"

    k = 0
    for key, value in fc_dict.iteritems():
        k += 1
        print "%s\t%s\t%s" % (k, key, value)
    print "----------"

    i = 0
    fc_dict = defaultdict(list)
    for fcid in handmade_fcids:
        if not fcid in fcids:
            i += 1
            #print ">>> %s no match in billing query" % fcid
            #print allfcdetails_report[fcid]
            fc_dict[fcid.split('_')[0]].append(fcid)

    print "----------"
    print "-- %s lanes found in handmade report do not match in billing query" % i
    print "----------"

    k = 0
    for key, value in fc_dict.iteritems():
        k += 1
        print "%s\t%s\t%s" % (k, key, value)
    print "----------"
    
    for key, value in handmade_statuses.iteritems():
        print key
        print len(value)
        #print "%s\t%s" % (key, value)
    print "----------"
    for key, value in statuses.iteritems():
        print key
        print len(value)
        #print "%s\t%s" % (key, value)
    print "----------"
    
    #print allfcdetails_report['A5M1G_Lane1']
    #for i in range(1,2):
    #    details = allfcdetails_report['A5M1G_Lane%s' % i][0].split('|')
    #    print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t" % (details[8], details[4], details[9][-1:], details[10], details[3], details[1], details[2], details[5], details[13] )


if __name__ == '__main__':
    main()

