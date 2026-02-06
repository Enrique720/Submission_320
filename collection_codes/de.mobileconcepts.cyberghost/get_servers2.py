import requests
import json
import sys
import time

outdir = "."

country_codes = []

in_file = "country_codes.txt"


with open(in_file, "r") as f:
    for line in f:
        country_codes.append(line.strip())

headers = {
    "accept": "application/json; charset=UTF-8",
    "x-app-key": "2321624eecd93aacdd70203266f01b92887745",
    "x-machine-id": "e5e737d898251340ee5c30cb18896e01",
    "x-machine-name": "Pixel XL",
    "user-agent": "okhttp/4.11.0",
    "authorization": 'OAuth oauth_version="1.0", oauth_signature_method="PLAINTEXT", oauth_consumer_key="", oauth_signature="", oauth_token=""',
    "accept-encoding": "gzip"
}

for country in country_codes:
    path = f""

    try:
        response = requests.get(path, headers=headers)

    except Exception as e:
        print(f"Error fetching servers for country {country}: {e}")
        continue

    with open(f"{outdir}/{country}_servers.json", "w") as f:
        json.dump(json.loads(response.text), f, indent=4)
    
    time.sleep(5)
