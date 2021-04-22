from tetpyclient import RestClient
import json
import urllib3
import sys

# Access vars
API_ENDPOINT = "https://plx.cisco.com"
CREDENTIALS_FILE = './api_credentials.json' # Create this file if it doesn't exist
APP_NAME = 'yourappname'
JSON_FILE = './conversations.json'

urllib3.disable_warnings()

try:
    file = open(CREDENTIALS_FILE, 'r')
except IOError:
    print('There was an error opening file {}'.format(CREDENTIALS_FILE))
    sys.exit(1)

try:
    rc = RestClient(API_ENDPOINT, credentials_file=CREDENTIALS_FILE, verify=False)
except:
    print("Can't create RC client. Are the following variables correct?")
    print("API_ENDPOINT: {}".format(API_ENDPOINT))
    print("CREDENTIALS_FILE: {}".format(CREDENTIALS_FILE))
    sys.exit(1)

# Fetch Application ID
resp = rc.get('/openapi/v1/applications/')
if resp.status_code == 200:
    parsed_resp = json.loads(resp.content)
    for app in parsed_resp:
        if app['name'] == APP_NAME:
            APP_ID = app['id']
else:
    print('Response code is not 200: {}'.format(resp.status_code))
    sys.exit(1)


# Fetch latest ADM version
try:
    resp = rc.get('/openapi/v1/applications/{}'.format(APP_ID))
except:
    print('Application not found: {}'.format(APP_NAME))
    sys.exit()
latest_adm = json.loads(resp.content)['latest_adm_version']

# Request Payload
req_payload = {
    "version": latest_adm,
    "dimensions": ["src_ip", "dst_ip", "port"],
    "metrics": ["byte_count", "packet_count"],
    "offset": "",
    "limit": 10
}

# Init conversation list and set a dummy offset
conversations = []
offset = 'init'

# Iterate through all responses using offsets and build the conversation list
while offset:
    resp = rc.post('/openapi/v1/conversations/{}'.format(APP_ID),
                   json_body=json.dumps(req_payload))
    if resp.status_code == 200:
        parsed_resp = json.loads(resp.content)
        try:
            offset = parsed_resp['offset']
        except:
            for item in parsed_resp['results']:
                conversations.append(item)
            break
        req_payload['offset'] = offset
        for item in parsed_resp['results']:
            conversations.append(item)
    else:
        print('Response code is not 200: {}'.format(resp.status_code))
        break

# Dump the conversation list to the JSON file
with open(JSON_FILE, 'w') as f:
    print('Found {} conversations. Dumping to file {}'.format(
        len(conversations), JSON_FILE))
    f.write(json.dumps(conversations, indent=4, sort_keys=True))