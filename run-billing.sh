#!/bin/bash

BASEDIR=$(dirname $0)
TEMPLATE=$BASEDIR/sql/gls-billing.sql
QUERY=$BASEDIR/billing/$(date +%Y%m)-billing.sql
CSVOUT=$BASEDIR/billing/$(date +%Y%m)-billing.csv

export PGPASSWORD=readonly

if ( sed 's/BILLING-DATE/'$(date +%Y-%m-%d)'/g' $TEMPLATE > $QUERY )
    then
    psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $QUERY` ) TO STDOUT WITH DELIMITER AS ';' CSV HEADER " > $CSVOUT || echo 'ERROR: Unable to run $QUERY' > $CSVOUT
    #for testting - quick query: psql -h lims -U readonly -d "clarityDB"  -c "COPY ( select * from researcher ) TO STDOUT WITH DELIMITER AS ';' CSV HEADER " > $CSVOUT
else
    echo 'ERROR: Unable to produce $QUERY from $TEMPLATE, no query ran' > $CSVOUT
fi
