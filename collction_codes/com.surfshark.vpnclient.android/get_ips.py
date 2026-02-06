import json
import sys
import socket

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python get_ips.py <path_to_json_file> <folder_name>")
        sys.exit(1)

    json_file_path = sys.argv[1]

    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            ips = []
            connections = []

            for item in data:
                #print(item['connectionName'])
                connections.append(item['connectionName'])
#                ips.append(get_ip_from_domain(item['connectionName']))

        # save the IPs to a txt file 
        folder_name = sys.argv[2]

        with open(f"{folder_name}/connections.txt", 'w') as conn_file:
            for conn in connections:
                conn_file.write(f"{conn}\n")

#        with open(f"{folder_name}/ips.txt", 'w') as ip_file:
#            for ip in ips:
#                ip_file.write(f"{ip}\n")


    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {json_file_path}")