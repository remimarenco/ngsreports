#!/bin/bash

BASEDIR=$(dirname $0)
SQLDIR=$BASEDIR/sql/
OUTPUTDIR=$BASEDIR/billing/

BILLING_DATE=201407
BILLING_PREVDATE=201406
GROUPREPORT_DATE=2014-06

BILLING_TEMPLATE=$SQLDIR/gls-billing.sql
BILLING_QUERY=$OUTPUTDIR/$BILLING_DATE-gls-billing.sql
BILLING_CSVOUT=$OUTPUTDIR/$BILLING_DATE-billing.csv
BILLING_LASTCVSOUT=$OUTPUTDIR/$BILLING_PREVDATE-billing.csv
COMPAREOUT=$OUTPUTDIR/$BILLING_DATE-compare-reports.out

QC_TEMPLATE=$SQLDIR/gls-qc.sql
QC_QUERY=$OUTPUTDIR/$BILLING_DATE-gls-qc.sql
QC_CSVOUT=$OUTPUTDIR/$BILLING_DATE-qc.csv

export PGPASSWORD=readonly

# billing ----------------------------------------------------------------------

# copy billing query
cp $BILLING_TEMPLATE $BILLING_QUERY

# billing report
psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $BILLING_QUERY` ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $BILLING_CSVOUT || echo 'ERROR: Unable to run $BILLING_QUERY' > $BILLING_CSVOUT
# test - quick/simple query: psql -h lims -U readonly -d "clarityDB"  -c "COPY ( select * from researcher ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $CSVOUT

# group reports
python $BASEDIR/reports.py --report=$BILLING_CSVOUT --date=$GROUPREPORT_DATE --outputdir=$BASEDIR

# billing report comparison & email notification
python $BASEDIR/autobilling.py --last-month-report=$BILLING_LASTCVSOUT --this-month-report=$BILLING_CSVOUT --output=$COMPAREOUT --email

# qc ---------------------------------------------------------------------------

# copy qc query
cp $QC_TEMPLATE $QC_QUERY

# qc report
psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $QC_QUERY` ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $QC_CSVOUT || echo 'ERROR: Unable to run $QC_QUERY' > $QC_CSVOUT




