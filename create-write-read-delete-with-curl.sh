export API_HOSTNAME={Replace-With-Qumulo-Cluster-Host}
export API_USER={Replace-With-Qumulo-Api-User}
export API_PASSWORD={Replace-With-Qumulo-Api-User}

# Login using the credentials above.
curl -sX POST \
       -H "Content-Type: application/json" \
       -k https://$API_HOSTNAME:8000/v1/session/login \
       -d "{\"username\": \"$API_USER\", \"password\": \"$API_PASSWORD\"}"

# set up the bearer token. requires jq command line tool for parsing json.
export API_TOKEN=$(curl -sX POST \
       -H "Content-Type: application/json" \
       -k https://$API_HOSTNAME:8000/v1/session/login \
       -d "{\"username\": \"$API_USER\", \"password\": \"$API_PASSWORD\"}" | jq -r '.bearer_token')

# create file
curl -X POST \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer $API_TOKEN" \
       -k https://$API_HOSTNAME:8000/v1/files/%2F/entries/ \
       -d "{
            \"action\": \"CREATE_FILE\",
            \"name\": \"test-file1.txt\"
        }"

# write to file
curl -X PUT \
       -H "Content-Type: application/octet-stream" \
       -H "Authorization: Bearer $API_TOKEN" \
       -k https://$API_HOSTNAME:8000/v1/files/%2Ftest-file1.txt/data \
       -d "Is it file, or is it object? You decide.
       "

# read from file
curl -X GET \
       -H "Authorization: Bearer $API_TOKEN" \
       -k https://$API_HOSTNAME:8000/v1/files/%2Ftest-file1.txt/data

# delete file
curl -X DELETE \
       -H "Authorization: Bearer $API_TOKEN" \
       -k https://$API_HOSTNAME:8000/v1/files/%2Ftest-file1.txt
