import requests
import sys

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

path = ""
headers = {
    "x-api-version": "3.4",
    "user-agent": "Android/ipvanish/4.1.11.0.258087-ipv-gm",
    "x-client": "ipvanish",
    "x-client-version": "4.1.11.0.258087-ipv-gm",
    "x-platform": "Android",
    "x-platform-version": "34",
    "accept-encoding": "gzip"
}

# D cide whether to use GET or POST based on the API requirements
#re ponse = requests.get(path, headers=headers)
response = requests.get(path, headers=headers)

with open(f"{outdir}/servers.json", "w") as f:
    f.write(response.text)
