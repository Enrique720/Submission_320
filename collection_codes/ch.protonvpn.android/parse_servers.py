import json
import sys

if len(sys.argv) != 3:
    print("Usage: python script.py <json_file> <out_dir>")
    sys.exit(1)

json_file = sys.argv[1]
outdir = sys.argv[2]

with open(json_file, "r") as f:
    data = json.load(f)

entry_ips = []
exit_ips = []
domains = []

for log_server in data['LogicalServers']:
    for server in log_server['Servers']:
        entry_ips.append(server['EntryIP'])
        exit_ips.append(server['ExitIP'])
        domains.append(server['Domain'])

with open(f"{outdir}/entry_ips.txt", "w") as f:
    for ip in entry_ips:
        f.write(f"{ip}\n")

with open(f"{outdir}/exit_ips.txt", "w") as f:
    for ip in exit_ips:
        f.write(f"{ip}\n")
        
with open(f"{outdir}/domains.txt", "w") as f:
    for domain in domains:
        f.write(f"{domain}\n")
