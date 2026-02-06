import json
import sys

# filename: servers.py file for browsec. 
if len(sys.argv) != 3:
    print (f"Usage: python3 {sys.argv[0]} <filename> <output_file>")

filename = sys.argv[1]
outfile = sys.argv[2]

with open(filename, 'r') as f:
    data = json.load(f)

servers = json.loads(data['entries']['servers'])
servers_ru = json.loads(data['entries']['servers_RU'])
countries = servers['countries']

countries_ru = servers_ru['countries']

ips = []
domains = []

for k,v in countries.items():
    if 'servers' in v.keys():
        domains.append(v['servers'][0]['host'])
        ip_list = v['servers'][0]['ip']
        for ip in ip_list:
            ips.append(ip) 

    if 'premium_servers' in v.keys():
        domains.append(v['premium_servers'][0]['host'])
        ip_list = v['premium_servers'][0]['ip']
        for ip in ip_list:
            ips.append(ip) 

ips_ru = []

for k,v in countries_ru.items():
    if 'servers' in v.keys():
        domains.append(v['servers'][0]['host'])
        ip_list = v['servers'][0]['ip']
        for ip in ip_list:
            ips_ru.append(ip) 

    if 'premium_servers' in v.keys():
        domains.append(v['premium_servers'][0]['host'])
        ip_list = v['premium_servers'][0]['ip']
        for ip in ip_list:
            ips_ru.append(ip) 

with open(outfile, 'w') as f:
    for ip in ips:
        f.write(f"{ip}\n")

with open(f"{outfile}_ru", 'w') as f:
    for ip in ips_ru:
        f.write(f"{ip}\n")

#print(domains)
#print(ips)

print(len(set(ips)))
print(len(set(ips_ru)))
print(len(set(ips + ips_ru)))