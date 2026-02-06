import requests
import sys
import time 
import json

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

path = ""
non_premium_path = ""
headers = {
    "content-length": "0",
    "accept-encoding": "gzip",
    "user-agent": "okhttp/4.9.1"
}

response = requests.get(path, headers=headers)

with open(f"{outdir}/servers.json", "w") as f:
    json.dump(json.loads(response.text), f, indent=4)


response_non_premium = requests.get(non_premium_path, headers=headers)

with open(f"{outdir}/non_premium_servers.json", "w") as f:
    json.dump(json.loads(response_non_premium.text), f, indent=4)
