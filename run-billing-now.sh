#!/bin/bash

BASEDIR=$(dirname $0)
source $BASEDIR/billing.sh

BILLING_DATE=201410
BILLING_PREVDATE=201409
GROUPREPORT_DATE=2014-09

run $BILLING_DATE $BILLING_PREVDATE $GROUPREPORT_DATE

