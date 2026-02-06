import requests
import sys
import json

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

path = ""
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

data = {
    "action": "example_body", 
}

# Decide whether to use GET or POST based on the API requirements
#response = requests.get(path, headers=headers)
response = requests.post(path, headers=headers, json=data)

with open(f"{outdir}/servers.json", "w") as f:
    #f.write(response.text)
    json.dump(response.json(), f, indent=4)
