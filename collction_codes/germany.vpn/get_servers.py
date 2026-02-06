import requests
import sys
import json

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

path = ""
headers = {
    "app-id": "",
    "accept": "application/json",
    "cache-control": "no-cache",
    "accept-encoding": "gzip",
    "user-agent": "okhttp/5.0.0-alpha.14"
}


# Decide whether to use GET or POST based on the API requirements
response = requests.get(path, headers=headers)

with open(f"{outdir}/servers.json", "w") as f:
    json.dump(response.json(), f, indent=4)

ss_path = ""

response = requests.get(ss_path, headers=headers)

with open(f"{outdir}/servers_ss.json", "w") as f:
    json.dump(response.json(), f, indent=4)

wg_path = ""

response = requests.get(wg_path, headers=headers)

with open(f"{outdir}/servers_wg.json", "w") as f:
    json.dump(response.json(), f, indent=4)