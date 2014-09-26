#!/bin/bash

query() {
    TEMPLATE=$1
    QUERY=$2
    CSVOUT=$3
    
    # copy query
    cp $TEMPLATE $QUERY

    # run query
    export PGPASSWORD=readonly
    psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $QUERY` ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $CSVOUT || echo "ERROR: Unable to run $QUERY" > $CSVOUT
    # test - quick/simple query: psql -h lims -U readonly -d "clarityDB"  -c "COPY ( select * from researcher ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $CSVOUT
}

run() {
    BILLING_DATE=$1
    BILLING_PREVDATE=$2
    GROUPREPORT_DATE=$3
    
    BASEDIR=$(dirname $0)
    SQLDIR=$BASEDIR/sql/
    OUTPUTDIR=$BASEDIR/billing/

    BILLING_TEMPLATE=$SQLDIR/gls-billing.sql
    BILLING_QUERY=$OUTPUTDIR/$BILLING_DATE-gls-billing.sql
    BILLING_CSVOUT=$OUTPUTDIR/$BILLING_DATE-billing.csv
    BILLING_LASTCVSOUT=$OUTPUTDIR/$BILLING_PREVDATE-billing.csv
    COMPAREOUT=$OUTPUTDIR/$BILLING_DATE-compare-reports.out

    ACCOUNT_TEMPLATE=$SQLDIR/gls-account.sql
    ACCOUNT_QUERY=$OUTPUTDIR/$BILLING_DATE-gls-account.sql
    ACCOUNT_CSV=$OUTPUTDIR/$BILLING_DATE-account.csv
    
    PRICES_CSV=$BASEDIR/pricing/PricingSummaryTable.txt

    QC_TEMPLATE=$SQLDIR/gls-qc.sql
    QC_QUERY=$OUTPUTDIR/$BILLING_DATE-gls-qc.sql
    QC_CSVOUT=$OUTPUTDIR/$BILLING_DATE-qc.csv

    # billing query
    query $BILLING_TEMPLATE $BILLING_QUERY $BILLING_CSVOUT 

    # account query
    query $ACCOUNT_TEMPLATE $ACCOUNT_QUERY $ACCOUNT_CSV

    # write reports, comparison & send email notification
    python $BASEDIR/reports.py --report=$BILLING_CSVOUT --previous-report=$BILLING_LASTCVSOUT --accounts=$ACCOUNT_CSV --prices=$PRICES_CSV --date=$GROUPREPORT_DATE --outputdir=$BASEDIR --email

    # qc query
    query $QC_TEMPLATE $QC_QUERY $QC_CSVOUT
}

