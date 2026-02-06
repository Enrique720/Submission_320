import requests
import sys
import json

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

path = ""
headers = {
    "zoog-fp": "",
    "Accept-Language": "en",
    "Host": "api.zoogvpn.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": "android 3.8.4"
}

# Decide whether to use GET or POST based on the API requirements
response = requests.get(path, headers=headers)

with open(f"{outdir}/servers.json", "w") as f:
    json.dump(response.json(), f, indent=4)
