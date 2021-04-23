from tetpyclient import RestClient
import json
import urllib3
import sys

# Access vars
API_ENDPOINT = "https://plx.cisco.com"

# Create this file if it doesn't exist
CREDENTIALS_FILE = './api_credentials.json'
SCOPE_NAME = 'DusLab:OpenCart'
INVENTORY_FILE = './inventory.json'

urllib3.disable_warnings()

try:
    file = open(CREDENTIALS_FILE, 'r')
except IOError:
    print('There was an error opening file {}'.format(CREDENTIALS_FILE))
    sys.exit(1)

try:
    rc = RestClient(
        API_ENDPOINT, credentials_file=CREDENTIALS_FILE, verify=False)
except:
    print("Can't create RC client. Are the following variables correct?")
    print("API_ENDPOINT: {}".format(API_ENDPOINT))
    print("CREDENTIALS_FILE: {}".format(CREDENTIALS_FILE))
    sys.exit(1)


# Init inventory item list

inventory_items = list()

# Build Payload

req_payload = {
    "scopeName": SCOPE_NAME,
    "limit": 10,
    "filter": {"type": "or",
               "filters": [
                   {"type": "eq", "field": "agent_type", "value": "ENFORCER"}
               ]
               }
}

# Init objects list and set a dummy offset
objects = []
offset = 'init'

# Iterate through all responses using offsets and build the inventory list based on payload filters
while offset:
    resp = rc.post('/openapi/v1/inventory/search',
                   json_body=json.dumps(req_payload))
    if resp.status_code == 200:
        parsed_resp = json.loads(resp.content)
        try:
            offset = parsed_resp['offset']
        except:
            for item in parsed_resp['results']:
                objects.append(item)
            break

        req_payload['offset'] = offset
        for item in parsed_resp['results']:
            objects.append(item)
    else:
        print('Response code is not 200: {}'.format(resp.status_code))
        break

# Iterate through the objects and build the results JSON file

for item in objects:
    packages = rc.get(
        '/openapi/v1/workload/{0}/packages'.format(item["uuid"]))
    vulnerabilities = rc.get(
        '/openapi/v1/workload/{0}/vulnerabilities'.format(item["uuid"]))

    if packages.status_code == 200:
        parsed_packages = json.loads(packages.content)

    else:
        print('Response code is not 200: {}'.format(packages.status_code))
        sys.exit(1)

    if vulnerabilities.status_code == 200:
        vuln_list = list()
        parsed_vulnerabilities = json.loads(vulnerabilities.content)
        for vuln in parsed_vulnerabilities:
            try:
                v3_score = vuln["v3_score"]
            except:
                v3_score = "N/A"
            vuln_list.append({
                "cve_id": vuln["cve_id"],
                "v3_score": v3_score,
                "package_infos": vuln["package_infos"]
            })
    else:
        print('Response code is not 200: {}'.format(
            vulnerabilities.status_code))
        sys.exit(1)

    inventory_items.append({
        "uuid": item["uuid"],
        "hostname": item["host_name"],
        "ip": item["ip"],
        "agent-type": item["agent_type"],
        "platform": item["os"],
        "packages": parsed_packages,
        "vulnerabilities": vuln_list
    })

# Dump the conversation list to the JSON file
with open(INVENTORY_FILE, 'w') as f:
    print('Found {} items. Dumping to file {}'.format(
        len(inventory_items), INVENTORY_FILE))
    f.write(json.dumps(inventory_items, indent=4, sort_keys=True))
