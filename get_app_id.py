from tetpyclient import RestClient
import json
import urllib3

# Access vars
API_ENDPOINT="https://plx.cisco.com"
CREDENTIALS_FILE='./api_credentials.json'

urllib3.disable_warnings()
rc = RestClient(API_ENDPOINT, credentials_file=CREDENTIALS_FILE, verify=False)

resp = rc.get('/openapi/v1/applications/')

#Print all applications
if resp.status_code == 200:
    parsed_resp = json.loads(resp.content)
    print(json.dumps(parsed_resp, indent=4, sort_keys=True))