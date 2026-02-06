#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path
from typing import Dict, Set, Tuple, Any, Optional, List
from datetime import datetime

BASE_DIR = Path("../../data/com.surfshark.vpnclient.android")
IN_CSV = Path("com.surfshark.vpnclient.android.csv")
OUT_CSV = Path("surfshark_servers_protocols.csv")

LOG_DIRNAME = "logs"
SERVERS_JSON = "servers.json"

# [2025-11-05 08:10:04] nslookup result for us-chi.prod.surfshark.com:
NSLOOKUP_LINE_RE = re.compile(r"nslookup result for\s+([A-Za-z0-9.-]+)\s*:", re.IGNORECASE)
IPV4_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")


def date_to_dirname(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%m/%d/%Y")
    return f"{dt.month:02d}_{dt.day:02d}_{dt.year:04d}"


def load_json_any(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"WARN: could not parse JSON: {path} ({e})")
        return None
    except Exception as e:
        print(f"WARN: error reading {path}: {e}")
        return None


def build_ip_to_host_map_from_logs(log_dir: Path) -> Dict[str, str]:
    """
    Scan logs ONCE and map each seen IP to the currently active nslookup hostname.
    Works for lines containing:
      - 'Address: <ip>' (nslookup output)
      - '[...] Resolved IP: <ip>' (your logger)
      - '[...] New IP seen: <ip>' etc.
    """
    ip_to_host: Dict[str, str] = {}
    if not log_dir.is_dir():
        return ip_to_host

    for log_file in sorted(log_dir.glob("*.txt")):
        current_host: Optional[str] = None
        try:
            with log_file.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = NSLOOKUP_LINE_RE.search(line)
                    if m:
                        current_host = m.group(1).strip().lower()
                        continue

                    if not current_host:
                        continue

                    m_ip = IPV4_RE.search(line)
                    if m_ip:
                        ip = m_ip.group(1)
                        # keep first mapping found (stable); change to assignment for "latest"
                        ip_to_host.setdefault(ip, current_host)
        except Exception as e:
            print(f"WARN: could not read log {log_file}: {e}")

    return ip_to_host


def protocols_from_server_obj(obj: Dict[str, Any]) -> Set[str]:
    """
    Based on your snippet, Surfshark entries include:
      - connectionName: "us-chi.prod.surfshark.com"
      - pubKey: ... (WireGuard)
    If you later find explicit OpenVPN/IKEv2 fields, add them here.

    Returns set of protocol labels, e.g. {"wireguard"}.
    """
    out: Set[str] = set()

    # WireGuard heuristic: pubKey present
    pub = obj.get("pubKey")
    if isinstance(pub, str) and pub.strip():
        out.add("wireguard")

    # If you discover explicit fields, uncomment/adapt:
    # proto = obj.get("protocol")
    # if isinstance(proto, str) and proto.strip():
    #     out.add(proto.strip().lower())

    return out


def build_connection_to_protocols(servers_json: Path) -> Dict[str, Set[str]]:
    """
    servers.json appears to be a LIST of server objects (per your start-of-file snippet).
    Build:
      connectionName(lower) -> {protocols}
    """
    out: Dict[str, Set[str]] = {}
    data = load_json_any(servers_json)
    if not isinstance(data, list):
        return out

    for obj in data:
        if not isinstance(obj, dict):
            continue
        conn = obj.get("connectionName")
        if not isinstance(conn, str) or not conn.strip():
            continue
        conn = conn.strip().lower()

        prots = protocols_from_server_obj(obj)
        if prots:
            out.setdefault(conn, set()).update(prots)
        else:
            # keep empty mapping out by default
            out.setdefault(conn, set())

    return out


def main() -> None:
    if not BASE_DIR.is_dir():
        raise SystemExit(f"Base dir not found: {BASE_DIR.resolve()}")
    if not IN_CSV.exists():
        raise SystemExit(f"Input CSV not found: {IN_CSV.resolve()}")

    total = 0
    bad_date = 0
    missing_dir = 0
    missing_servers_json = 0
    no_host = 0
    no_protocols = 0

    # Cache per date dir
    cache_ip_to_host: Dict[str, Dict[str, str]] = {}
    cache_conn_to_prots: Dict[str, Dict[str, Set[str]]] = {}

    with IN_CSV.open("r", encoding="utf-8", newline="") as fin, \
         OUT_CSV.open("w", encoding="utf-8", newline="") as fout:

        reader = csv.reader(fin)
        writer = csv.writer(fout)
        writer.writerow(["date", "ip", "protocols"])

        # skip first line (e.g. ",0")
        next(reader, None)

        for row in reader:
            if not row or len(row) < 2:
                continue

            ip = (row[0] or "").strip()
            date_str = (row[1] or "").strip()
            if not ip or not date_str:
                continue

            total += 1

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

            # Load per-date maps once
            if dir_name not in cache_ip_to_host:
                cache_ip_to_host[dir_name] = build_ip_to_host_map_from_logs(date_dir / LOG_DIRNAME)

            if dir_name not in cache_conn_to_prots:
                sjson = date_dir / SERVERS_JSON
                if not sjson.exists():
                    missing_servers_json += 1
                    cache_conn_to_prots[dir_name] = {}
                else:
                    cache_conn_to_prots[dir_name] = build_connection_to_protocols(sjson)

            hostname = cache_ip_to_host[dir_name].get(ip)
            if not hostname:
                no_host += 1
                writer.writerow([date_str, ip, ""])
                continue

            prots = cache_conn_to_prots[dir_name].get(hostname.lower(), set())
            if not prots:
                no_protocols += 1

            writer.writerow([date_str, ip, ",".join(sorted(prots))])

            if total % 5000 == 0:
                print(f"Processed {total} rows...")

    print(f"\nWrote output to {OUT_CSV.resolve()}")
    print(f"Total rows processed: {total}")
    print(f"Bad date rows: {bad_date}")
    print(f"Missing date directories: {missing_dir}")
    print(f"Missing servers.json (per-date): {missing_servers_json}")
    print(f"IPs not found in logs (no hostname): {no_host}")
    print(f"Hostnames found but no protocols found in servers.json: {no_protocols}")


if __name__ == "__main__":
    main()
