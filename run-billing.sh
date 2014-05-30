#!/bin/bash

BASEDIR=$(dirname $0)

BILLING_DATE=$(date +%Y%m)
BILLING_PREVDATE=$(date --date="$(date +%Y-%m-15) -1 month" +%Y%m)
BILLING_SQLDATE=$(date +%Y-%m-05)
GROUPREPORT_DATE=$(date --date="$(date +%Y-%m-15) -1 month" +%Y-%m)

BILLING_TEMPLATE=$BASEDIR/sql/gls-billing.sql
BILLING_QUERY=$BASEDIR/billing/$BILLING_DATE-billing.sql
BILLING_CSVOUT=$BASEDIR/billing/$BILLING_DATE-billing.csv
BILLING_LASTCVSOUT=$BASEDIR/billing/$BILLING_PREVDATE-billing.csv
COMPAREOUT=$BASEDIR/billing/$BILLING_DATE-compare-reports.out

QC_TEMPLATE=$BASEDIR/sql/gls-qc.sql
QC_QUERY=$BASEDIR/billing/$BILLING_DATE-qc.sql
QC_CSVOUT=$BASEDIR/billing/$BILLING_DATE-qc.csv

export PGPASSWORD=readonly

# billing ----------------------------------------------------------------------
if ( sed 's/BILLING-DATE/'$BILLING_SQLDATE'/g' $BILLING_TEMPLATE > $BILLING_QUERY )
    then
    # billing report
    psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $BILLING_QUERY` ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $BILLING_CSVOUT || echo 'ERROR: Unable to run $BILLING_QUERY' > $BILLING_CSVOUT
    # test - quick/simple query: psql -h lims -U readonly -d "clarityDB"  -c "COPY ( select * from researcher ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $CSVOUT
    # group reports
    python $BASEDIR/group_reports.py --report=$BILLING_CSVOUT --date=$GROUPREPORT_DATE --outputdir=$BASEDIR
    # billing report comparison & email notification
    python $BASEDIR/autobilling.py --last-month-report=$BILLING_LASTCVSOUT --this-month-report=$BILLING_CSVOUT --output=$COMPAREOUT --email
else
    echo 'ERROR: Unable to produce $BILLING_QUERY from $BILLING_TEMPLATE, no query ran' > $BILLING_CSVOUT
fi

# qc ---------------------------------------------------------------------------
if ( sed 's/BILLING-DATE/'$BILLING_SQLDATE'/g' $QC_TEMPLATE > $QC_QUERY )
    then
    # qc report
    psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $QC_QUERY` ) TO STDOUT WITH DELIMITER AS E'\t' CSV HEADER " > $QC_CSVOUT || echo 'ERROR: Unable to run $QC_QUERY' > $QC_CSVOUT

else
    echo 'ERROR: Unable to produce $QC_QUERY from $QC_TEMPLATE, no query ran' > $QC_CSVOUT
fi
