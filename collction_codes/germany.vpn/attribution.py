import json
import glob
import sys
from collections import defaultdict
import pandas as pd

filename = 'servers.json'
ss_filename = 'servers_ss.json'
wg_filename = 'servers_wg.json'

ddir = sys.argv[1]

ips = defaultdict(list)

with open(f"{ddir}/{filename}", "r") as f:
    data = json.load(f)
    for server in data:
        ip = server.get('ip')
        ips[ip].append('openvpn')

with open(f"{ddir}/{ss_filename}", "r") as f:
    data = json.load(f)
    for server in data:
        ip = server.get('ip')
        ips[ip].append('shadowsocks')

with open(f"{ddir}/{wg_filename}", "r") as f:
    data = json.load(f)
    for server in data:
        ip = server.get('ip')
        ips[ip].append('wireguard')

arr = []

for k, v in ips.items():
    arr.append((k, ','.join(v)))

df = pd.DataFrame(arr, columns=['ip', 'protocols'])
df.to_csv(f"{ddir}/attribution.csv", index=False)
