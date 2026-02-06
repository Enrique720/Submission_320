import csv
import json
import requests
import time
from datetime import datetime
import os
import sys

API_TOKEN = os.environ["CENSYS_API_TOKEN"]
ORG_ID = os.environ["CENSYS_ORG_ID"]

if len(sys.argv) < 2:
    print(f"Usage: python3 {sys.argv[0]} <filename>")
    exit(1)

base_path = sys.argv[1]
INPUT_CSV = f"{base_path}.csv"
OUTPUT_FILE = f"{base_path}.json"

BASE_URL = "https://api.platform.censys.io/v3/global/asset/host/{ip}"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "X-Organization-ID": f"{ORG_ID}",
    "Accept": "application/vnd.censys.api.v3.host.v1+json"
}

def format_date_rfc3339(date_str):
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y")
        # end-of-day to match the original script behavior
        return dt.strftime("%Y-%m-%dT23:59:59Z")
    except ValueError as e:
        print(f"Invalid date '{date_str}': {e}")
        return None

def main():
    unique_entries = set()

    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                ip = row[0].strip()
                raw_date = row[1].strip()
                if ip and raw_date:
                    unique_entries.add((ip, raw_date))

    print(f"Found {len(unique_entries)} unique IP/date pairs.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for idx, (ip, raw_date) in enumerate(unique_entries, 1):
            rfc_date = format_date_rfc3339(raw_date)
            if not rfc_date:
                continue

            print(f"[{idx}/{len(unique_entries)}] Fetching {ip} at {rfc_date}...")

            params = {"at_time": rfc_date}

            resp = requests.get(
                BASE_URL.format(ip=ip),
                headers=HEADERS,
                params=params
            )

            if resp.status_code == 200:
                out.write(json.dumps(resp.json()) + "\n")
                print(" -> snapshot saved (includes ports/services)")
            elif resp.status_code == 404:
                print(" -> host not found at that time")
            elif resp.status_code == 429:
                print(" -> rate limited — sleeping 60s")
                time.sleep(60)
            else:
                try:
                    print(" -> error", resp.status_code, resp.json())
                except:
                    print(" -> error", resp.status_code, resp.text)

            time.sleep(1)

    print("Done.")

if __name__ == "__main__":
    main()

