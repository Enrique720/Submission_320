import requests
import time
import json
import sys
import socket

headers = {
    "user-agent": "Core/1.19.1 PureVPN/8.70.8 Android",
    "content-type": "application/x-www-form-urlencoded",
    "content-length": "59",
    "accept-encoding": "gzip"
}

URL = ""


def main(outfolder):
    # access tokens
    token_url = f"{URL}/auth/v1/accessToken"

    
    response = requests.post(
        token_url,
        headers=headers,
        data="secretKey="
    )

    response_json = json.loads(response.content)
    xaccess_token = response_json['body']["accessToken"]

    cities_url = f"{URL}/inventory/v2/cities/android"
    cities_headers = {
        "user-agent": "AtomSDK/4.8.0-beta07 PureVPN/8.70.8 Android",
        "accept-encoding" : "gzip",
        "x-accesstoken": xaccess_token
    }

    time.sleep(5)
    server_response = requests.get(cities_url, headers=cities_headers)
    data = json.loads(server_response.content)

    with open(f"{outfolder}/servers.json", "w") as f:
        json.dump(data["body"], f, indent=4)

    server_names = []

    for city in data["body"]['cities']:
        for server in city['protocols']:
            try:
                # iterate through servers in each city
                for s in server['dns']:
                    server_names.append(s['name'])
            except:
                continue

    with open(f"{outfolder}/server_names.txt", "w") as f:
        for server in server_names: 
            f.write(server+ "\n")

    time.sleep(5)
    server_response = requests.get(f"{URL}/inventory/v1/server/acknowledgmentServer", headers=cities_headers)

    print(server_response.text)

if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("Usage: python get_servers.py <outfile>")
        sys.exit(1)
    
    outfolder = sys.argv[1] 
        
    main(outfolder)
