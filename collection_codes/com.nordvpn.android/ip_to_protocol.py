#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from typing import Dict, Set, Tuple, Iterable, Any, Optional
from datetime import datetime

BASE_DIR = Path("../../data/com.nordvpn.android")
IN_CSV = Path("com.nordvpn.android.csv")
OUT_CSV = Path("nordvpn_servers_protocols.csv")


def find_json_file(date_dir: Path) -> Optional[Path]:
    """
    NordVPN date directory contains one JSON file.
    If multiple exist, prefer servers.json, else pick the largest file.
    """
    candidates = sorted(date_dir.glob("*.json"))
    if not candidates:
        return None

    for p in candidates:
        if p.name.lower() == "servers.json":
            return p

    # If multiple, choose the largest (usually the main payload)
    candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0]


def load_json(json_path: Path) -> Dict[str, Any]:
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        print(f"WARN: could not parse JSON: {json_path} ({e})")
        return {}
    except Exception as e:
        print(f"WARN: error reading {json_path}: {e}")
        return {}


def normalize_tech_identifier(identifier: str) -> Optional[str]:
    """
    Convert NordVPN 'technologies[].identifier' values into base protocol names.

    Examples:
      openvpn_udp -> openvpn
      openvpn_tcp -> openvpn
      openvpn_xor_udp -> openvpn
      wireguard_udp -> wireguard
      ikev2 -> ikev2
      proxy_ssl -> proxy
      socks -> socks
      nordwhisper -> nordwhisper

    Return None to drop unknown identifiers if you want strict output.
    """
    if not isinstance(identifier, str):
        return None
    ident = identifier.strip().lower()
    if not ident:
        return None

    if ident.startswith("openvpn"):
        return "openvpn"
    if ident.startswith("wireguard"):
        return "wireguard"
    if ident.startswith("ikev2"):
        return "ikev2"
    if ident.startswith("proxy"):
        return "proxy"
    if ident.startswith("socks"):
        return "socks"

    # Keep single-token identifiers like "nordwhisper"
    if "_" not in ident:
        return ident

    # Fallback: take first token (safe default)
    return ident.split("_", 1)[0]


def extract_server_ips(server_obj: Dict[str, Any]) -> Set[str]:
    """
    Each server has: "ips": [{"type": "entry", "ip": {"ip": "x.x.x.x", ...}}, ...]
    Return all IPv4/IPv6 strings found.
    """
    out: Set[str] = set()
    ips = server_obj.get("ips", [])
    if not isinstance(ips, list):
        return out

    for item in ips:
        if not isinstance(item, dict):
            continue
        ip_obj = item.get("ip")
        if isinstance(ip_obj, dict):
            ip_str = ip_obj.get("ip")
            if isinstance(ip_str, str) and ip_str.strip():
                out.add(ip_str.strip())
    return out


def extract_server_tech_ids(server_obj: Dict[str, Any]) -> Set[int]:
    """
    Each server has: "technologies": [{"id": 3, "status": "online", ...}, ...]
    Return IDs for technologies that apply to this server.
    """
    out: Set[int] = set()
    techs = server_obj.get("technologies", [])
    if not isinstance(techs, list):
        return out

    for t in techs:
        if not isinstance(t, dict):
            continue
        tid = t.get("id")
        if isinstance(tid, int):
            # If you want to filter by status, uncomment:
            # status = t.get("status")
            # if isinstance(status, str) and status.lower() not in ("online", ""):
            #     continue
            out.add(tid)
    return out


def build_tech_id_to_identifier(data: Dict[str, Any]) -> Dict[int, str]:
    """
    Top-level has: "technologies": [{"id": 3, "identifier": "openvpn_udp", ...}, ...]
    Map id -> identifier.
    """
    out: Dict[int, str] = {}
    techs = data.get("technologies", [])
    if not isinstance(techs, list):
        return out

    for t in techs:
        if not isinstance(t, dict):
            continue
        tid = t.get("id")
        ident = t.get("identifier")
        if isinstance(tid, int) and isinstance(ident, str) and ident.strip():
            out[tid] = ident.strip()
    return out


def load_ip_to_protocols(json_path: Path) -> Dict[str, Set[str]]:
    """
    Build ip -> set(base_protocol_names) for the NordVPN JSON.
    """
    data = load_json(json_path)
    if not data:
        return {}

    tech_map = build_tech_id_to_identifier(data)

    servers = data.get("servers", [])
    if not isinstance(servers, list):
        return {}

    ip_map: Dict[str, Set[str]] = {}

    for s in servers:
        if not isinstance(s, dict):
            continue

        ips = extract_server_ips(s)
        if not ips:
            continue

        tech_ids = extract_server_tech_ids(s)
        if not tech_ids:
            continue

        prot_names: Set[str] = set()
        for tid in tech_ids:
            ident = tech_map.get(tid)
            if not ident:
                continue
            base = normalize_tech_identifier(ident)
            if base:
                prot_names.add(base)

        if not prot_names:
            continue

        for ip in ips:
            ip_map.setdefault(ip, set()).update(prot_names)

    return ip_map


def read_date_ip_pairs(csv_path: Path) -> Set[Tuple[str, str]]:
    """
    Reads CSV and returns a set of (date_str, ip) pairs.
    - Skips first line.
    - Assumes rows like: ip,date
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

    # Cache per directory so multiple IPs for same date don't re-parse JSON
    cache: Dict[str, Dict[str, Set[str]]] = {}

    results: Dict[Tuple[str, str], Set[str]] = {}

    missing_dir = 0
    missing_json = 0
    missing_ip = 0

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
            json_path = find_json_file(date_dir)
            if not json_path:
                print(f"WARN: no JSON file found in {date_dir.resolve()}")
                missing_json += 1
                cache[dir_name] = {}
            else:
                cache[dir_name] = load_ip_to_protocols(json_path)

        ip_map = cache[dir_name]
        prots = ip_map.get(ip, set())
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
    print(f"Dates with missing JSON: {missing_json}")
    print(f"(date,ip) pairs where IP not found / no protocols: {missing_ip}")


if __name__ == "__main__":
    main()
