ngsreports
==========

Monthly billing report 
Outputs:
- query 201402-billing.sql in billing/
- report 201402-billing.csv in billing/
- comparison 201402-compare-reports.out in billing/

    ```shell
    sed 's/BILLING-DATE/'$(date +%Y-%m-%d)'/g' sql/gls-billing.sql > $(date +%Y%m)-billing.sql
    psql -h lims -U readonly -d "clarityDB"  -c "COPY ( `cat $(date +%Y%m)-billing.sql` ) TO STDOUT WITH DELIMITER AS ';' CSV HEADER " > $(date +%Y%m)-billing.csv
    
    ```shell
    last month: date --date="$(date +%Y-%m-15) -1 month" +%Y%m
    this month: date +%Y%m
    python compare_billing_reports.py --last-report=$(date --date="$(date +%Y-%m-15) -1 month" +%Y%m)-billing.csv --this-report=$(date +%Y%m)-billing.csv > $(date +%Y%m)-compare-reports.out
    
    ./run-billing.sh
    
Monthly research group reports
Outputs:
- 201402-groupname-report.html in groups/

     ```shell
     python lab_reports.py --report=$(date +%Y%m)-billing.csv --output=groups/
     
     
CRUK Cambridge Institute set up http://uk-cri-lsol03.crnet.org:8080/solexa/home/mib-cri/solexa/ngsreports/billing/