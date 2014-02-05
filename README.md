ngsreports
==========

Monthly billing report:

    sed 's/BILLING-DATE/'$(date +%Y-%m-%d)'/g' sql/gls-billing.sql > $(date +%Y%m)-billing.sql
    psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $(date +%Y%m)-billing.sql` ) TO STDOUT WITH DELIMITER AS ';' CSV HEADER " > $(date +%Y%m)-billing.csv
    
Monthly billing comparison report
    
    last month: date --date="$(date +%Y-%m-15) -1 month" +%Y%m
    this month: date +%Y%m
    python compare_billing_reports.py --last-report=$(date --date="$(date +%Y-%m-15) -1 month" +%Y%m)-billing.csv --this-report=$(date +%Y%m)-billing.csv > $(date +%Y%m)-compare-reports.out
    
Monthly research group reports

     python lab_reports.py --report=$(date +%Y%m)-billing.csv    