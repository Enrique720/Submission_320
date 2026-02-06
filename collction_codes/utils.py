def fetch_json(url, headers=None):
    import requests

    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0",
            "Host": "firebaseio.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
            }

    try: 
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


import socket
import dns.resolver
def get_all_ips_dns(domain):
    ips = []
    for record_type in ['A', 'AAAA']:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            ips.extend([r.to_text() for r in answers])
        except dns.resolver.NoAnswer:
            continue
    return ips

def get_all_ips_round_robin(domain, attempts=5):
    all_ips = set()
    for _ in range(attempts):
        all_ips.update(get_all_ips_dns(domain))
    return list(all_ips)

# Example
print(get_all_ips_round_robin("al-tia.prod.surfshark.com"))