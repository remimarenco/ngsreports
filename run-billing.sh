#!/bin/bash

BASEDIR=$(dirname $0)
source $BASEDIR/billing.sh

BILLING_DATE=$(date --date="$(date +%Y-%m-15) -1 month" +%Y%m)
BILLING_PREVDATE=$(date --date="$(date +%Y-%m-15) -2 month" +%Y%m)
GROUPREPORT_DATE=$(date --date="$(date +%Y-%m-15) -1 month" +%Y-%m)
NOTIFICATIONS=$BASEDIR/pricing/BillingNotificationContacts.txt

run $BILLING_DATE $BILLING_PREVDATE $GROUPREPORT_DATE $NOTIFICATIONS