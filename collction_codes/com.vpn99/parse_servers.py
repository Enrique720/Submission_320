import json
import sys


def find_all_by_key(obj, key):
    """Recursively find all values for the given key in a JSON-like structure."""
    results = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                results.append(v)
            results.extend(find_all_by_key(v, key))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_all_by_key(item, key))

    return results

def main(input_file, output_file):
    print(input_file,output_file)

    try:
        with open(input_file,'r') as f:
            data = json.load(f)

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        exit(1)

    ips = []

    for server in data:
        ips.append(server['ip'])

    
    with open(output_file,'w') as f:
        for ip in ips:
            f.write(f"{ip}\n")
    
    return 0    

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <input_file> <output_file>")
        exit(1)

    main(sys.argv[1],sys.argv[2])
