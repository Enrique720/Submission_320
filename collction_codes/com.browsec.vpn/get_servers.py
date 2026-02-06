import json
import time
import requests
import sys

if (len(sys.argv) != 2):
    print("Usage: python3 get_servers.py <outdir>")
    sys.exit(1)

outdir = sys.argv[1]


headers = {
    "Accept": "application/json",
    "Content-Encoding": "gzip",
    "Cache-Control": "no-cache",
    "X-Android-Package": "com.browsec.vpn",
    "x-firebase-client": "",
    "X-Android-Cert": "",
    "x-goog-api-key": "",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; Pixel XL Build/RQ1A.210105.003)",
    "Host": "firebaseinstallations.googleapis.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Length": "134"
}

content = {
    "appId": "1:355082820262:android:e48d2046170ca25f",
    "authVersion": "FIS_v2",
    "fid": "dJFOqjlqTV2Vke0YZgKT8I",
    "sdkVersion": "a:17.2.0"
}

api_endpoint = ""

response = requests.post(api_endpoint, headers=headers, data=json.dumps(content))


data_json = json.loads(response.content)

authToken = data_json['authToken']['token']


server_enpoint = ""

server_headers = {
  "X-Goog-Api-Key": "",
  "X-Android-Package": "com.browsec.vpn",
  "X-Android-Cert": "",
  "X-Google-GFE-Can-Retry": "yes",
  "X-Goog-Firebase-Installations-Auth": authToken,
  "Content-Type": "application/json",
  "Accept": "application/json",
  "X-Firebase-RC-Fetch-Type": "BASE/1",
  "Content-Length": "945",
  "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; Pixel XL Build/RQ1A.210105.003)",
  "Host": "firebaseremoteconfig.googleapis.com",
  "Connection": "Keep-Alive",
  "Accept-Encoding": "gzip"
}


data_payload = {
    "analyticsUserProperties": {
        "ABI": "x86_64",
        "app_lang": "en",
        "currency": "pkr",
        "first_run_date": "20240830",
        "first_run_version_code": "567",
        "first_run_version_name": "5.105",
        "premium": "false",
        "protocol_openvpn": "true",
        "protocol_shadowsocks": "true",
        "protocol_xray": "true",
        "ssl_protocol": "TLSv1.3"
    },
    "appBuild": "567",
    "appId": "1:355082820262:android:e48d2046170ca25f",
    "appInstanceId": "dJFOqjlqTV2Vke0YZgKT8I",
    "appInstanceIdToken": authToken,
    "appVersion": "5.105",
    "countryCode": "US",
    "firstOpenTime": "2024-08-30T23:00:00.000Z",
    "languageCode": "en-US",
    "packageName": "com.browsec.vpn",
    "platformVersion": "30",
    "sdkVersion": "21.6.3",
    "timeZone": "Asia/Karachi"
}

time.sleep(5)
response = requests.post(server_enpoint, headers=server_headers, data=json.dumps(data_payload))
data = json.loads(response.content)
with open(f"{outdir}/servers.json", "w") as f:
    json.dump(data, f, indent=4)

data_payload_2 = {
    "appVersion": "5.117",
    "firstOpenTime": "2025-12-14T06:00:00.000Z",
    "timeZone": "GMT",
    "appInstanceIdToken": authToken,
    "languageCode": "en-US",
    "appBuild": "691",
    "appInstanceId": "fLpkepiKQomuI5El5wZ6_Q",
    "countryCode": "US",
    "analyticsUserProperties": {
        "premium": "false",
        "ABI": "x86_64",
        "protocol_xray": "true",
        "protocol_shadowsocks": "false",
        "currency": "usd",
        "app_lang": "en",
        "first_run_version_name": "5.117",
        "android_sdk": "34",
        "ssl_protocol": "TLSv1.3",
        "first_run_version_code": "691",
        "first_run_date": "20251214",
        "protocol_kcp": "false"
    },
    "appId": "1:355082820262:android:e48d2046170ca25f",
    "platformVersion": "34",
    "sdkVersion": "22.1.2",
    "packageName": "com.browsec.vpn"
}

response = requests.post(server_enpoint, headers=server_headers, data=json.dumps(data_payload_2))
data = json.loads(response.content)
with open(f"{outdir}/servers_ru.json", "w") as f:
    json.dump(data, f, indent=4)