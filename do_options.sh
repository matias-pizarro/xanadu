#!/usr/local/bin/bash
endpoints=(sizes regions images ssh_keys)
for i in "${endpoints[@]}"; do
  url=`printf "https://api.digitalocean.com/v2/%s" $i`
  curl -X GET -H "Content-Type: application/json" -H "Authorization: Bearer ${DO_API_TOKEN}" $url | python -mjson.tool
done