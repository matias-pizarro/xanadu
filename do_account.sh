#!/usr/local/bin/bash
endpoints=(account/keys account)
for i in "${endpoints[@]}"; do
  url=`printf "https://api.digitalocean.com/v2/%s" $i`
  curl -X GET -H "Content-Type: application/json" -H "Authorization: Bearer ${DO_API_TOKEN}" $url | python -mjson.tool
done