from time import time
import requests
import sys
import json

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <outdir>")
    sys.exit(1)

outdir = sys.argv[1]

token_path = ""
path = ""

headers = {
    "X-Nimbus-ClientId": "",
    "X-Nimbus-UUID": "",
    "Content-type": "application/json",
    "User-Agent": "com.bitdefender.vpn/2.2.5.157 (Android 14; Pixel XL/UP1A.231105.003.A1)",
    "Host": "nimbus.bitdefender.net",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Length": "297",
}

data = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "enable_vpn",
    "params": {
        "user_agreement": 0,
        "utc_offset": "+00:00",
        "tokens_expired": True,
        "check_bad_email": False,
        "connect_source": {
            "user_token": "",
            "device_id": "",
            "app_id": "com.bitdefender.vpn"
        }
    }
}

# Decide whether to use GET or POST based on the API requirements
#response = requests.get(path, headers=headers)
response = requests.post(token_path, headers=headers, json=data)

#print(response.text)
bearer_token = response.json().get("result", {}).get("access_token")
#print(bearer_token)

headers = {
    "x-api-version": "3.4",
    "x-api-key": "",
    "authorization": f"Bearer {bearer_token}",
    "user-agent": "Android/api-key/2.3.8.257314",
    "x-client": "api-key",
    "x-client-version": "2.3.8.257314",
    "x-platform": "Android",
    "x-platform-version": "34",
    "accept-encoding": "gzip"
}

time.sleep(5)
response_paths = requests.get(path, headers=headers)
print(response_paths.text)


with open(f"{outdir}/servers.json", "w") as f:
    json.dump(response_paths.json(), f, indent=4)

path = ""

time.sleep(5)
response_full = requests.get(path, headers=headers)
with open(f"{outdir}/servers_full.json", "w") as f:
    json.dump(response_full.json(), f, indent=4)