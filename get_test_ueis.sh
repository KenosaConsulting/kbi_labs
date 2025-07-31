#!/bin/bash
echo "Getting test UEIs from database..."

# Get UEIs from your enriched companies
sudo -u postgres psql -d kbi_enriched -t -c "
SELECT uei, organization_name 
FROM enriched_companies 
WHERE uei IS NOT NULL 
AND uei != '' 
LIMIT 10;
" | while read uei name; do
    if [ ! -z "$uei" ]; then
        echo "Testing UEI: $uei - $name"
        curl -s "http://localhost:8001/api/v3/usaspending/search/$uei" | jq -c '{status: .status, total_awards: .data.summary.total_awards, total_amount: .data.summary.total_amount}'
        sleep 1
    fi
done
