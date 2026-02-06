import requests
import json
import sys

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

path = ""

headers = {
    "accept": "application/json; charset=UTF-8",
    "x-app-key": "2321624eecd93aacdd70203266f01b92887745",
    "content-type": "application/json; charset=UTF-8",
    "content-length": "43",
    "accept-encoding": "gzip",
    "user-agent": "okhttp/4.11.0"
}

data = {
    "key": ""
}

response = requests.post(path, headers=headers, json=data)

with open(f"{outdir}/servers.json", "w") as f:
    json.dump(json.loads(response.text), f, indent=4)

