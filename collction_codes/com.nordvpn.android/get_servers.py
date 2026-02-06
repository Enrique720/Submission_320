import json
import requests
import sys


count_url = ""

def fetch_json(url):
    headers = {
        "Authorization": "",
        "User-Agent": "NordApp android (playstoreMobile/7.6.1) Android 13",
        "Nord-Agent": '{"App":"NordVPN","Platform":"Android","AppVersion":"7.6.1","API version":"33","DeviceInfo":"x86_64","AdditionalInfo":"flavor-playstoreMobile"}',
        "Host": "",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    try: 
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


def main(outdir):
    server_data = fetch_json(count_url)
   
    n_servers = server_data['count']

    servers_url = f""

    servers_data = fetch_json(servers_url) 

    servers = servers_data['servers']

    ips = [server['ips'][0]['ip']['ip'] for server in servers]

    with open(f"{outdir}/servers.json", 'w') as f:
        json.dump(servers_data, f)

    with open(f"{outdir}/servers_ips.txt", 'w') as f:
        f.write("\n".join(ips))


if __name__ == "__main__":

    if (len(sys.argv) != 2):
        print(f"Usage: python3 {sys.argv[0]} <outdir>")
        exit(1)    

    main(sys.argv[1])
