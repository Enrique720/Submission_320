from time import time
import requests
import json
import sys


ENDPOINT = ""

SESSION_ENPOINT = ""

LOG_ENDPOINT = ""

payload = {
    "Payload": {
        "vpn-android-v4-challenge-0": {
            "appLa27 Aug 2025,ng": "en",
            "deviceName": 118819746192,
            "isDarkmodeOn": False,
            "isJailbreak": False,
            "keyboards": [
                "com.android.inputmethod.latin"
            ],
            "preferredContentSize": "1.0",
            "regionCode": "US",
            "storageCapacity": 32.0,
            "timezone": "GMT",
            "timezoneOffset": 0,
            "v": "2.0.6"
        }
    }
}


sign_payload = {
    "Payload": {
        "vpn-android-v4-challenge-0": {
            "appLang": "en",
            "deviceName": 118819746192,
            "isDarkmodeOn": False,
            "isJailbreak": False,
            "keyboards": [
                "com.android.inputmethod.latin"
            ],
            "preferredContentSize": "1.0",
            "regionCode": "US",
            "storageCapacity": 32.0,
            "timezone": "Asia/Kathmandu",
            "timezoneOffset": -345,
            "type": "me.proton.core.challenge.data.frame.ChallengeFrame.Device",
            "v": "2.0.6"
        }
    }
}

def get_headers():
    headers = {
        "x-pm-appversion" : "android-vpn@5.5.68.0+play",
        "x-pm-locale": "en",
        "user-agent": "ProtonVPN/5.5.68.0 (Android 14; Pixel XL)",
        "accept": "application/vnd.protonmail.v1+json",
        "content-type": "application/json; charset=utf-8",
        "content-length": "290",
        "accept-encoding": "gzip"
    }
    return headers

def main(outdir):
    headers = get_headers()

    
    # Get session for request the API endpoint
    response = requests.post(SESSION_ENPOINT, headers=headers, json=payload)
    #print(response.status_code)
    #print(response.json())

    response_headers = response.headers
    
    response_json = response.json()

    Bearer = response_json['AccessToken']
    uid = response_json['UID']
    cookie = response_headers['set-cookie'].split(';')[0] + "; Tag=default"
   
   
    # Get VPn scope by credentialess log in:
    headers = {
        "x-pm-country": "US",
        "x-pm-netzone": "172.93.132.0",
        "if-modified-since" : "Thu, 01 Jan 1970 00:00:00 GMT",
        "x-pm-appversion": "android-vpn@5.5.68.0+play",
        "x-pm-locale": "en",
        "user-agent": "ProtonVPN/5.5.68.0 (Android 13)",
        "accept": "application/vnd.protonmail.v1+json",
        "x-pm-uid": uid,
        "authorization": f"Bearer {Bearer}",
        "accept-encoding": "gzip",
        "cookie": cookie
    }

    auth_request = requests.post(LOG_ENDPOINT, headers=headers, json=sign_payload)
    vpn_bearer = auth_request.json()['AccessToken']

    # Get the server list
    headers['authorization'] = f"Bearer {vpn_bearer}"
    time.sleep(5) 
    server_response = requests.get(ENDPOINT, headers=headers).json()

    try:
        path=""
        response_tier0 = requests.get(path+str(0), headers=headers)
        time.sleep(5)
        response_tier2 = requests.get(path+str(2), headers=headers)

    except: 
        print("failed to fetch tier 0 and tier 2 servers")


    with open(outdir + "/servers.json", "w") as f:
        json.dump(server_response, f, indent=4)
    
    with open(outdir + "/tier0.json", "w") as f:
        try:
            json.dump(response_tier0.json(), f, indent=4)
        except:
            print("failed to dump tier 0 and tier 2 servers")    
        
    with open(outdir + "/tier2.json", "w") as f:
        try:
            json.dump(response_tier2.json(), f, indent=4)
        except:
            print("failed to dump tier 0 and tier 2 servers")    
            
    try:
        time.sleep(5)
        response_servers_count = requests.get("", headers=headers)
        response_servers_count.raise_for_status()
    except:
        print("failed to fetch servers count")
    with open(outdir + "/servers_count.json", "w") as f:
        try:
            json.dump(response_servers_count.json(), f, indent=4)
        except:
            print("failed to dump servers count")

if __name__=="__main__":

    if len(sys.argv) != 2:
        print("Usage: python get_servers.py <out_dir>")
        sys.exit(1)

    try:
        main(sys.argv[1])
    except Exception as e:
        print(f"An error occurred: {e}")
    