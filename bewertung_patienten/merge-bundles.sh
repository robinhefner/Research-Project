#!/bin/bash
# merge-bundles.sh

# Prüfen, ob jq installiert ist
if ! command -v jq &> /dev/null; then
    echo "Error: jq ist nicht installiert. Bitte installieren mit 'winget install jqlang.jq'"
    exit 1
fi

# Der jq-Filter als Variable
JQ_FILTER='
reduce inputs as $bundle (
    {"resourceType": "Bundle", "type": "transaction", "entry": []};
    if $bundle.entry then .entry += $bundle.entry else . end
)
| .entry |= map(
    (.resource.resourceType) as $resourceType
    | . + {"request": {"method": "POST", "url": $resourceType}}
    | del(.fullUrl, .search)
)
| .total = (.entry | length)
'

# Ausführung: Nutzt --null-input (-n) für reduce inputs
jq -n "$JQ_FILTER" "$@"