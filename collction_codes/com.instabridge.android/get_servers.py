import requests
import sys
import json
import time

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)


premium_path = ""
path = ""

outdir = sys.argv[1]

headers = {
    "content-length": "0",
    "accept-encoding": "gzip",
    "user-agent": "okhttp/4.12.0"
}

try:
    response = requests.post(premium_path, headers=headers)
    response_json = json.loads(response.text)
    with open(f"{outdir}/servers_premium.json", "w") as f:
        json.dump(response_json, f, indent=4)
except requests.exceptions.RequestException as e:
    print(f"Error making request to {premium_path}: {e}")
    sys.exit(1)

time.sleep(5)
try:
    response = requests.get(path, headers=headers)
    response_json = json.loads(response.text)

    with open(f"{outdir}/servers_non_premium.json", "w") as f:
        json.dump(response_json, f, indent=4)

except requests.exceptions.RequestException as e:
    print(f"Error making request to {premium_path}: {e}")
    sys.exit(1)