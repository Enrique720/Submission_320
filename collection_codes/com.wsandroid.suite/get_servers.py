import requests
import sys
import json
import os
import time

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

path = ""
headers = {
    "ghostbear-tech": "none",
    "polarbear-app-version": "9.5.1.7",
    "polarbear-app-id": "com.wsandroid.suite",
    "polarbear-platform-version": "34",
    "polarbear-platform": "Android",
    "polarbear-sdk-version": "3.4.24",
    "authorization": "",
    "content-type": "application/json; charset=UTF-8",
    "content-length": "207",
    "accept-encoding": "gzip",
    "user-agent": "okhttp/4.12.0"
}

data = {
    "partner": "",
    "token": ""
}

# Decide whether to use GET or POST based on the API requirements
response = requests.post(path, headers=headers, json=data)

auth_token = response.headers.get("authorization")

regions_path = ""

headers={
    "ghostbear-tech": "none",
    "polarbear-app-version": "9.5.1.7",
    "polarbear-app-id": "com.wsandroid.suite",
    "polarbear-platform-version": "34",
    "polarbear-platform": "Android",
    "polarbear-sdk-version": "3.4.24",
    "authorization": auth_token,
    "accept-encoding": "gzip",
    "user-agent": "okhttp/4.12.0"
}

response = requests.get(regions_path, headers=headers)


regions = []
region_prefix = []
for region in response.json():
    regions.append(region['country_iso']) 
    region_prefix.append(region['dns_prefix'])


with open(f"{outdir}/regions_output.json", "w") as f:  
    json.dump(response.json(), f, indent=4)


with open(f"{outdir}/regions.txt", "w") as f:
    for region in regions:
        f.write(f"{region}\n")

with open(f"{outdir}/region_prefix.txt", "w") as f:
    for prefix in region_prefix:
        f.write(f"{prefix}.removed_for_submission.com\n")

apis = []
os.makedirs(f"{outdir}/regions", exist_ok=True)
for region in regions:
    response = requests.get(f"")
    if response.status_code == 200:
        apis.append(response.json()['ipsec']) 

        with open(f"{outdir}/regions/{region}.json", "w") as f:
            json.dump(response.json(), f, indent=4)
        time.sleep(5)

    else:
        print(f"Failed to fetch VPNs for region {region}: {response.status_code} - {response.text}")

with open(f"{outdir}/server_names.txt", "w") as f:
    for api in apis:
        f.write(f"{api}\n")