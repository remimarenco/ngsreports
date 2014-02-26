#!/bin/bash

BASEDIR=$(dirname $0)
TEMPLATE=$BASEDIR/sql/gls-billing.sql
QUERY=$BASEDIR/billing/$(date +%Y%m)-billing.sql
CSVOUT=$BASEDIR/billing/$(date +%Y%m)-billing.csv
LASTCVSOUT=$BASEDIR/billing/$(date --date="$(date +%Y-%m-15) -1 month" +%Y%m)-billing.csv
COMPAREOUT=$BASEDIR/billing/$(date +%Y%m)-compare-reports.out

export PGPASSWORD=readonly

if ( sed 's/BILLING-DATE/'$(date +%Y-%m-05)'/g' $TEMPLATE > $QUERY )
    then
    # billing report
    psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $QUERY` ) TO STDOUT WITH DELIMITER AS ';' CSV HEADER " > $CSVOUT || echo 'ERROR: Unable to run $QUERY' > $CSVOUT
    # test - quick/simple query: psql -h lims -U readonly -d "clarityDB"  -c "COPY ( select * from researcher ) TO STDOUT WITH DELIMITER AS ';' CSV HEADER " > $CSVOUT
    # group reports
    python $BASEDIR/group_reports.py --report=$CSVOUT --date=$(date --date="$(date +%Y-%m-15) -1 month" +%Y-%m) --outputdir=$BASEDIR
    # billing report comparison & email notification
    python $BASEDIR/autobilling.py --last-month-report=$LASTCVSOUT --this-month-report=$CSVOUT --output=$COMPAREOUT --email
else
    echo 'ERROR: Unable to produce $QUERY from $TEMPLATE, no query ran' > $CSVOUT
fi
