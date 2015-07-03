#!/bin/bash

BASEDIR=$(dirname $0)

NGSMAILINGLIST_QUERY=$BASEDIR/sql/gls-ngsmailinglist.sql
NGSMAILINGLIST_OUT=$BASEDIR/reports/gls-ngsmailinglist.txt

export PGPASSWORD=readonly

# ngsmailinglist ---------------------------------------------------------------
psql -h genomicsequencing.cruk.cam.ac.uk -U readonly -d "clarityDB"  -c "COPY ( `cat $NGSMAILINGLIST_QUERY` ) TO STDOUT" > $NGSMAILINGLIST_OUT

