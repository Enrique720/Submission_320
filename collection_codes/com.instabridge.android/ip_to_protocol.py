#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from typing import Dict, Set, Tuple, Iterable, Any
from datetime import datetime

BASE_DIR = Path("../../data/com.instabridge.android")
IN_CSV = Path("com.instabridge.android.csv")          # input
OUT_CSV = Path("instabridge_servers_protocols.csv")   # output

NON_PREM = "servers_non_premium.json"
PREM = "servers_premium.json"


def iter_server_entries(json_path: Path) -> Iterable[Dict[str, Any]]:
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"WARN: could not parse JSON: {json_path} ({e})")
        return []
    except Exception as e:
        print(f"WARN: error reading {json_path}: {e}")
        return []


def true_protocols(server_obj: Dict[str, Any]) -> Set[str]:
    prot = server_obj.get("protocols", {})
    if not isinstance(prot, dict):
        return set()
    return {k for k, v in prot.items() if v is True}


def load_ip_to_protocols(json_path: Path) -> Dict[str, Set[str]]:
    """
    Builds ip -> set(true_protocols) for a single JSON file.
    If an IP occurs multiple times in the file, protocols are unioned.
    """
    ip_map: Dict[str, Set[str]] = {}
    for entry in iter_server_entries(json_path):
        if not isinstance(entry, dict):
            continue
        ip = entry.get("ip")
        if not ip or not isinstance(ip, str):
            continue
        prots = true_protocols(entry)
        if not prots:
            continue
        ip_map.setdefault(ip, set()).update(prots)
    return ip_map


def read_date_ip_pairs(csv_path: Path) -> Set[Tuple[str, str]]:
    """
    Reads com.instabridge.android.csv and returns a set of (date_str, ip) pairs.
    - Skips first line.
    - Accepts rows like: ip,date
    """
    pairs: Set[Tuple[str, str]] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)

        # Skip the first line (e.g., ",0")
        try:
            next(reader)
        except StopIteration:
            return pairs

        for row in reader:
            if not row or len(row) < 2:
                continue
            ip = (row[0] or "").strip()
            date_str = (row[1] or "").strip()
            if ip and date_str:
                pairs.add((date_str, ip))
    return pairs


def date_to_dirname(date_str: str) -> str:
    """
    CSV date is assumed to be like 11/05/2025 (MM/DD/YYYY).
    Directory name is MM_DD_YYYY, e.g., 11_05_2025.
    """
    dt = datetime.strptime(date_str, "%m/%d/%Y")
    return f"{dt.month:02d}_{dt.day:02d}_{dt.year:04d}"


def main() -> None:
    if not BASE_DIR.exists() or not BASE_DIR.is_dir():
        raise SystemExit(f"Base dir not found or not a directory: {BASE_DIR.resolve()}")

    if not IN_CSV.exists():
        raise SystemExit(f"Input CSV not found: {IN_CSV.resolve()}")

    date_ip_pairs = read_date_ip_pairs(IN_CSV)
    print(f"Loaded {len(date_ip_pairs)} unique (date, ip) pairs from {IN_CSV.resolve()}")

    # Cache per directory to avoid re-parsing JSON for multiple IPs on same date
    cache: Dict[str, Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]] = {}

    results: Dict[Tuple[str, str], Set[str]] = {}

    missing_dir = 0
    missing_ip = 0
    dup_prem_non = 0

    for (date_str, ip) in sorted(date_ip_pairs, key=lambda x: (x[0], x[1])):
        try:
            dir_name = date_to_dirname(date_str)
        except ValueError:
            print(f"WARN: could not parse date '{date_str}' (expected MM/DD/YYYY)")
            missing_dir += 1
            results[(date_str, ip)] = set()
            continue

        date_dir = BASE_DIR / dir_name
        if not date_dir.is_dir():
            print(f"WARN: directory not found for date '{date_str}': {date_dir.resolve()}")
            missing_dir += 1
            results[(date_str, ip)] = set()
            continue

        if dir_name not in cache:
            non_map = load_ip_to_protocols(date_dir / NON_PREM)
            prem_map = load_ip_to_protocols(date_dir / PREM)
            cache[dir_name] = (non_map, prem_map)

        non_map, prem_map = cache[dir_name]

        non_prots = non_map.get(ip, set())
        prem_prots = prem_map.get(ip, set())

        if non_prots and prem_prots:
            dup_prem_non += 1

        prots = set(non_prots) | set(prem_prots)
        if not prots:
            missing_ip += 1

        results[(date_str, ip)] = prots

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "ip", "protocols"])
        for (date_str, ip), prots in sorted(results.items(), key=lambda x: (x[0][0], x[0][1])):
            writer.writerow([date_str, ip, ",".join(sorted(prots))])

    print(f"\nWrote {len(results)} rows to {OUT_CSV.resolve()}")
    print(f"Dates with missing directory: {missing_dir}")
    print(f"(date,ip) pairs where IP not found / no true protocols: {missing_ip}")
    print(f"(date,ip) pairs present in BOTH premium & non-premium: {dup_prem_non}")


if __name__ == "__main__":
    main()
