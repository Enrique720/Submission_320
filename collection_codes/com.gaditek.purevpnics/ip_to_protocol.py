#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path
from typing import Dict, Set, Tuple, Any, Optional, List
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = Path("../../data/com.gaditek.purevpnics")
IN_CSV = Path("com.gaditek.purevpnics.csv")
OUT_CSV = Path("purevpnics_servers_protocols.csv")

LOG_DIRNAME = "logs"
SERVERS_JSON = "servers.json"

NSLOOKUP_LINE_RE = re.compile(r"nslookup result for\s+([A-Za-z0-9.-]+)\s*:", re.IGNORECASE)
IPV4_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")


def date_to_dirname(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%m/%d/%Y")
    return f"{dt.month:02d}_{dt.day:02d}_{dt.year:04d}"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def normalize_protocol_name(p: Any) -> Optional[str]:
    """
    IMPORTANT CHANGE:
      - Do NOT map UDP/TCP -> openvpn.
      - If they appear, keep them as 'udp' or 'tcp'.
      - Only map to openvpn if it explicitly says openvpn.
    """
    if not isinstance(p, str):
        return None
    s = p.strip().lower()
    if not s:
        return None

    if s in {"ikev", "ikev2", "ikev-2", "ike"}:
        return "ikev2"
    if s in {"wireguard", "wg"}:
        return "wireguard"

    # keep transport labels
    if s in {"udp", "tcp"}:
        return s

    # explicit openvpn
    if "openvpn" in s:
        return "openvpn"

    return s  # keep unknowns



def build_ip_to_host_map_from_logs(log_dir: Path) -> Dict[str, str]:
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
                        ip_to_host.setdefault(ip, current_host)
        except Exception:
            continue

    return ip_to_host


def build_dns_name_to_protocols(servers_json: Path) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    data = load_json(servers_json)
    if not data:
        return out

    cities = data.get("cities", [])
    if not isinstance(cities, list):
        return out

    for city in cities:
        if not isinstance(city, dict):
            continue
        prot_list = city.get("protocols", [])
        if not isinstance(prot_list, list):
            continue

        for prot_obj in prot_list:
            if not isinstance(prot_obj, dict):
                continue

            pnorm = normalize_protocol_name(prot_obj.get("protocol"))
            if not pnorm:
                continue

            dns_list = prot_obj.get("dns", [])
            if not isinstance(dns_list, list):
                continue

            for dns in dns_list:
                if not isinstance(dns, dict):
                    continue
                name = dns.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue
                name = name.strip().lower()
                out.setdefault(name, set()).add(pnorm)

    return out


def process_one_date(dir_name: str, rows: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str, str]]]:
    out_rows: List[Tuple[str, str, str]] = []

    date_dir = BASE_DIR / dir_name
    if not date_dir.is_dir():
        for date_str, ip in rows:
            out_rows.append((date_str, ip, ""))
        return dir_name, out_rows

    ip_to_host = build_ip_to_host_map_from_logs(date_dir / LOG_DIRNAME)
    dns_map = build_dns_name_to_protocols(date_dir / SERVERS_JSON)

    for date_str, ip in rows:
        host = ip_to_host.get(ip)
        if not host:
            out_rows.append((date_str, ip, ""))
            continue
        prots = dns_map.get(host, set())
        out_rows.append((date_str, ip, ",".join(sorted(prots))))

    return dir_name, out_rows


def main() -> None:
    if not BASE_DIR.is_dir():
        raise SystemExit(f"Base dir not found: {BASE_DIR.resolve()}")
    if not IN_CSV.exists():
        raise SystemExit(f"Input CSV not found: {IN_CSV.resolve()}")

    by_dir: Dict[str, List[Tuple[str, str]]] = {}
    bad_date_rows: List[Tuple[str, str]] = []

    with IN_CSV.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.reader(fin)
        next(reader, None)
        for row in reader:
            if not row or len(row) < 2:
                continue
            ip = (row[0] or "").strip()
            date_str = (row[1] or "").strip()
            if not ip or not date_str:
                continue
            try:
                dir_name = date_to_dirname(date_str)
            except ValueError:
                bad_date_rows.append((date_str, ip))
                continue
            by_dir.setdefault(dir_name, []).append((date_str, ip))

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["date", "ip", "protocols"])

        for date_str, ip in bad_date_rows:
            writer.writerow([date_str, ip, ""])

        with ProcessPoolExecutor(max_workers=1) as ex:
            futures = [ex.submit(process_one_date, d, rows) for d, rows in by_dir.items()]
            done = 0
            for fut in as_completed(futures):
                dir_name, out_rows = fut.result()
                for date_str, ip, prots in out_rows:
                    writer.writerow([date_str, ip, prots])
                done += 1
                print(f"Done {done}/{len(futures)}: {dir_name} ({len(out_rows)} rows)")

    print(f"\nWrote output to {OUT_CSV.resolve()}")


if __name__ == "__main__":
    main()