#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from typing import Dict, Set, Tuple, Iterable, Any, Optional
from datetime import datetime

BASE_DIR = Path("../../data/com.zoogvpn.android")
IN_CSV = Path("com.zoogvpn.android.csv")
OUT_CSV = Path("zoogvpn_servers_protocols.csv")

SERVERS_JSON = "servers.json"


def read_date_ip_pairs(csv_path: Path) -> Set[Tuple[str, str]]:
    """
    Reads CSV and returns a set of (date_str, ip) pairs.
    - Skips first line (e.g., ",0")
    - Assumes rows like: ip,date
    """
    pairs: Set[Tuple[str, str]] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)

        try:
            next(reader)  # skip first line
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
    CSV date like 11/05/2025 (MM/DD/YYYY) -> dir name 11_05_2025
    """
    dt = datetime.strptime(date_str, "%m/%d/%Y")
    return f"{dt.month:02d}_{dt.day:02d}_{dt.year:04d}"


def load_servers_list(json_path: Path) -> Iterable[Dict[str, Any]]:
    """
    Expects JSON like:
      { "error": false, "servers": [ {...}, {...} ] }
    Returns list under "servers" or [] on errors.
    """
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return []
        servers = data.get("servers", [])
        return servers if isinstance(servers, list) else []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"WARN: could not parse JSON: {json_path} ({e})")
        return []
    except Exception as e:
        print(f"WARN: error reading {json_path}: {e}")
        return []


def normalize_zoog_protocol_label(label: str) -> Optional[str]:
    """
    Convert Zoog protocol strings into normalized protocol *names* only.

    IMPORTANT CHANGE:
      - Do NOT map UDP/TCP -> openvpn anymore.
      - If they show up, keep them as "udp" or "tcp".
      - Only return "openvpn" if it explicitly says "openvpn".
    """
    if not isinstance(label, str):
        return None

    p = label.strip().lower()
    if not p:
        return None

    # Keep transport labels as-is
    if p in {"udp", "tcp"}:
        return p

    # Explicit protocol names
    if p in {"openvpn", "open_vpn", "open-vpn"}:
        return "openvpn"
    if p in {"ikev2", "ikev", "ike"}:
        return "ikev2"
    if p in {"wireguard", "wg"}:
        return "wireguard"
    if p == "dtls":
        return "dtls"

    # Shadowsocks / V2Ray / VMess / XRay variants (Zoog-specific naming)
    p_up = p.upper()
    if p_up.startswith("SS_"):
        if "SHADOWSOCKS" in p_up:
            return "shadowsocksr" if "SSR" in p_up else "shadowsocks"
        if "V2RAY" in p_up:
            return "v2ray"
        if "VMESS" in p_up:
            return "vmess"
        if "XR" in p_up:
            return "xray"
        return "shadowsocks"

    # Keep unknown labels (or return None if you want strict)
    return p



def protocols_from_server(server_obj: Dict[str, Any]) -> Set[str]:
    """
    Extract normalized protocol NAMES from a Zoog server.
    server_obj["protocols"] is expected to be a list of dicts:
      { "protocol": "UDP", "port": 1194, ... }
    We ignore port/configName/etc and only return normalized names.
    """
    out: Set[str] = set()
    plist = server_obj.get("protocols", [])
    if not isinstance(plist, list):
        return out

    for entry in plist:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("protocol")
        if not isinstance(raw, str):
            continue
        norm = normalize_zoog_protocol_label(raw)
        if norm:
            out.add(norm)

    return out


def load_ip_to_protocols(json_path: Path) -> Dict[str, Set[str]]:
    """
    Builds ip -> set(protocol_names) for one servers.json.
    If an IP occurs multiple times, protocol names are unioned.
    """
    ip_map: Dict[str, Set[str]] = {}

    for server in load_servers_list(json_path):
        if not isinstance(server, dict):
            continue

        ip = server.get("ip")
        if not isinstance(ip, str) or not ip.strip():
            continue
        ip = ip.strip()

        prots = protocols_from_server(server)
        if not prots:
            continue

        ip_map.setdefault(ip, set()).update(prots)

    return ip_map


def main() -> None:
    if not BASE_DIR.exists() or not BASE_DIR.is_dir():
        raise SystemExit(f"Base dir not found or not a directory: {BASE_DIR.resolve()}")

    if not IN_CSV.exists():
        raise SystemExit(f"Input CSV not found: {IN_CSV.resolve()}")

    date_ip_pairs = read_date_ip_pairs(IN_CSV)
    print(f"Loaded {len(date_ip_pairs)} unique (date, ip) pairs from {IN_CSV.resolve()}")

    cache: Dict[str, Dict[str, Set[str]]] = {}  # dir_name -> ip_map
    results: Dict[Tuple[str, str], Set[str]] = {}

    missing_dir = 0
    missing_ip = 0

    for (date_str, ip) in sorted(date_ip_pairs, key=lambda x: (x[0], x[1])):
        try:
            dir_name = date_to_dirname(date_str)
        except ValueError:
            print(f"WARN: could not parse date '{date_str}' (expected MM/DD/YYYY)")
            results[(date_str, ip)] = set()
            missing_dir += 1
            continue

        date_dir = BASE_DIR / dir_name
        if not date_dir.is_dir():
            print(f"WARN: directory not found for date '{date_str}': {date_dir.resolve()}")
            results[(date_str, ip)] = set()
            missing_dir += 1
            continue

        if dir_name not in cache:
            cache[dir_name] = load_ip_to_protocols(date_dir / SERVERS_JSON)

        prots = cache[dir_name].get(ip, set())
        if not prots:
            missing_ip += 1

        results[(date_str, ip)] = set(prots)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "ip", "protocols"])
        for (date_str, ip), prots in sorted(results.items(), key=lambda x: (x[0][0], x[0][1])):
            writer.writerow([date_str, ip, ",".join(sorted(prots))])

    print(f"\nWrote {len(results)} rows to {OUT_CSV.resolve()}")
    print(f"Dates with missing directory: {missing_dir}")
    print(f"(date,ip) pairs where IP not found / no protocols: {missing_ip}")


if __name__ == "__main__":
    main()
