ngsreports
==========

Requirements:
    - SVN installed in command line

_Monthly billing report_

Outputs in `billing/`:
- query `201402-billing.sql`
- report `201402-billing.csv`
- report comparison `201402-compare-reports.out`

    ```shell
    sed 's/BILLING-DATE/'$(date +%Y-%m-%d)'/g' sql/gls-billing.sql > $(date +%Y%m)-billing.sql
    psql -h genomicsequencing.cruk.cam.ac.uk -U readonly -d "clarityDB"  -c "COPY ( `cat $(date +%Y%m)-billing.sql` ) TO STDOUT WITH DELIMITER AS ';' CSV HEADER " > $(date +%Y%m)-billing.csv
    
    last month: date --date="$(date +%Y-%m-15) -1 month" +%Y%m
    this month: date +%Y%m
    python compare_billing_reports.py --last-report=$(date --date="$(date +%Y-%m-15) -1 month" +%Y%m)-billing.csv --this-report=$(date +%Y%m)-billing.csv > $(date +%Y%m)-compare-reports.out
    
    ./run-billing.sh
    ```
    
_Monthly research group reports_

Outputs in `groups/`:
- per group `201402-groupname-report.html`

     ```shell
     python lab_reports.py --report=$(date +%Y%m)-billing.csv --output=groups/
     ```
          
CRUK Cambridge Institute set up http://uk-cri-lsol03.crnet.org:8080/solexa/home/mib-cri/solexa/ngsreports/billing/