import json
import sys


def main(input_file, output_file):
    print(input_file,output_file)

    try:
        with open(input_file,'r') as f:
            data = json.load(f)

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        exit(1)


    ips = [] 

    for server in data['servers']:
        ips.append(server['ip_address'])
    
    with open(output_file,'w') as f:
        for ip in ips:
            f.write(f"{ip}\n")
    
    return 0    

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <input_file> <output_file>")
        exit(1)

    main(sys.argv[1],sys.argv[2])
