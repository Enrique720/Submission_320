import json
import sys

def parse_servers(input_file):
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    
    servers = data['servers']  

    ips = []    
    domains = []
    for server in servers:
        ips.append(server["ip_address"])
        domains.append(server["name"])
    
    return ips, domains


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    ips, domains = parse_servers(input_file)

    #with open(output_file, "w") as f:
    #    for ip, domain in zip(ips,domains):
    #        f.write(f"{ip},{domain}\n")

    with open(output_file, "w") as f:
        for ip in ips:
            f.write(f"{ip}\n")
