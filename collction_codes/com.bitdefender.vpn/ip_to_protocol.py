#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from typing import Dict, Set, Tuple, Any, Optional, List
from datetime import datetime

BASE_DIR = Path("../../data/com.bitdefender.vpn")
IN_CSV = Path("com.bitdefender.vpn.csv")
OUT_CSV = Path("bitdefender_vpn_servers_protocols.csv")

SERVERS_JSON = "servers.json"
SERVERS_FULL_JSON = "servers_full.json"


def date_to_dirname(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%m/%d/%Y")
    return f"{dt.month:02d}_{dt.day:02d}_{dt.year:04d}"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"WARN: JSON parse error: {path} ({e})")
        return None
    except Exception as e:
        print(f"WARN: error reading {path}: {e}")
        return None


def normalize_protocol_name(name: Any) -> Optional[str]:
    if not isinstance(name, str):
        return None
    s = name.strip().lower()
    return s if s else None


def load_ip_set_from_servers(servers_path: Path) -> Set[str]:
    data = load_json(servers_path)
    if not data:
        return set()

    servers = data.get("servers", [])
    if not isinstance(servers, list):
        return set()

    out: Set[str] = set()
    for s in servers:
        if not isinstance(s, dict):
            continue
        ip = s.get("ip_address")
        if isinstance(ip, str) and ip.strip():
            out.add(ip.strip())
    return out


def load_ip_to_protocols_from_full(full_path: Path) -> Dict[str, Set[str]]:
    data = load_json(full_path)
    if not data:
        return {}

    servers = data.get("servers", [])
    if not isinstance(servers, list):
        return {}

    ip_map: Dict[str, Set[str]] = {}
    for s in servers:
        if not isinstance(s, dict):
            continue

        ip = s.get("ip_address")
        if not isinstance(ip, str) or not ip.strip():
            continue
        ip = ip.strip()

        prots: Set[str] = set()
        prot_list = s.get("protocols", [])
        if isinstance(prot_list, list):
            for p in prot_list:
                if not isinstance(p, dict):
                    continue
                pname = normalize_protocol_name(p.get("name"))
                if pname:
                    prots.add(pname)

        if prots:
            ip_map.setdefault(ip, set()).update(prots)

    return ip_map


def list_date_dirs(base_dir: Path) -> List[Path]:
    # date dirs look like 11_05_2025
    return sorted([p for p in base_dir.iterdir() if p.is_dir()])


def build_global_ip_to_protocols(base_dir: Path) -> Dict[str, Set[str]]:
    """
    Scan all date dirs that have servers_full.json and build:
      ip -> {protocols}
    """
    global_map: Dict[str, Set[str]] = {}
    date_dirs = list_date_dirs(base_dir)

    scanned = 0
    for d in date_dirs:
        full_path = d / SERVERS_FULL_JSON
        if not full_path.exists():
            continue
        ip_map = load_ip_to_protocols_from_full(full_path)
        if not ip_map:
            continue

        for ip, prots in ip_map.items():
            global_map.setdefault(ip, set()).update(prots)

        scanned += 1
        if scanned % 25 == 0:
            print(f"Scanned {scanned} servers_full.json files...")

    print(f"Built global protocol index from {scanned} servers_full.json files.")
    return global_map


def main() -> None:
    if not BASE_DIR.is_dir():
        raise SystemExit(f"Base dir not found: {BASE_DIR.resolve()}")
    if not IN_CSV.exists():
        raise SystemExit(f"Input CSV not found: {IN_CSV.resolve()}")

    # Read all rows (we keep them to write in original order)
    rows: List[Tuple[str, str]] = []
    with IN_CSV.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.reader(fin)
        next(reader, None)  # skip first line (e.g., ",0")
        for r in reader:
            if not r or len(r) < 2:
                continue
            ip = (r[0] or "").strip()
            date_str = (r[1] or "").strip()
            if ip and date_str:
                rows.append((date_str, ip))

    print(f"Loaded {len(rows)} rows from {IN_CSV.resolve()}")

    # Per-date cache
    cache_allowed_ips: Dict[str, Set[str]] = {}
    cache_ip_to_prots: Dict[str, Dict[str, Set[str]]] = {}
    cache_has_full: Dict[str, bool] = {}

    bad_date = 0
    missing_dir = 0
    missing_servers = 0
    missing_full_dates = 0
    used_fallback = 0
    still_missing_protocols = 0

    # Build fallback index once (only used when a date has no servers_full.json)
    global_ip_to_prots = build_global_ip_to_protocols(BASE_DIR)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["date", "ip", "protocols"])

        for i, (date_str, ip) in enumerate(rows, start=1):
            try:
                dir_name = date_to_dirname(date_str)
            except ValueError:
                bad_date += 1
                writer.writerow([date_str, ip, ""])
                continue

            date_dir = BASE_DIR / dir_name
            if not date_dir.is_dir():
                missing_dir += 1
                writer.writerow([date_str, ip, ""])
                continue

            # Load servers.json ip-set once per date
            if dir_name not in cache_allowed_ips:
                allowed = load_ip_set_from_servers(date_dir / SERVERS_JSON)
                cache_allowed_ips[dir_name] = allowed
                if not allowed:
                    missing_servers += 1

            # Load servers_full.json mapping once per date (if present)
            if dir_name not in cache_has_full:
                full_path = date_dir / SERVERS_FULL_JSON
                if full_path.exists():
                    cache_has_full[dir_name] = True
                    cache_ip_to_prots[dir_name] = load_ip_to_protocols_from_full(full_path)
                else:
                    cache_has_full[dir_name] = False
                    cache_ip_to_prots[dir_name] = {}
                    missing_full_dates += 1

            # Optional: enforce membership in servers.json
            allowed_ips = cache_allowed_ips[dir_name]
            if allowed_ips and ip not in allowed_ips:
                # if it's not in servers.json, still write blank (your earlier logic)
                writer.writerow([date_str, ip, ""])
                continue

            # Try date-local mapping first
            prots = cache_ip_to_prots[dir_name].get(ip, set())

            # If date has no servers_full.json, fallback to global index
            if not prots and not cache_has_full[dir_name]:
                prots = global_ip_to_prots.get(ip, set())
                if prots:
                    used_fallback += 1

            if not prots:
                still_missing_protocols += 1

            writer.writerow([date_str, ip, ",".join(sorted(prots))])

            if i % 5000 == 0:
                print(f"Processed {i}/{len(rows)} rows...")

    print(f"\nWrote {len(rows)} rows to {OUT_CSV.resolve()}")
    print(f"Bad date rows: {bad_date}")
    print(f"Missing date directories: {missing_dir}")
    print(f"Dates where servers.json empty/missing: {missing_servers}")
    print(f"Dates missing servers_full.json: {missing_full_dates}")
    print(f"Rows filled via fallback from other dates: {used_fallback}")
    print(f"Rows still missing protocols: {still_missing_protocols}")


if __name__ == "__main__":
    main()
