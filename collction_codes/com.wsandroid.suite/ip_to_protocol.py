#!/usr/bin/env python3
import csv
import json
import re
import os
from pathlib import Path
from typing import Dict, Set, Tuple, Any, Optional, List
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = Path("../../data/com.wsandroid.suite")
IN_CSV = Path("com.wsandroid.suite.csv")
OUT_CSV = Path("wsandroid_suite_servers_protocols.csv")

REGIONS_DIRNAME = "regions"
LOG_DIRNAME = "logs"

NSLOOKUP_LINE_RE = re.compile(r"nslookup result for\s+([A-Za-z0-9.-]+)\s*:", re.IGNORECASE)
IP_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")


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


def infer_protocols(entry: Dict[str, Any]) -> Set[str]:
    """
    Return a SET of protocol labels for one vpn entry.

    Rules you asked for:
      - Only label openvpn if it explicitly mentions openvpn (not inferred from tcp/udp)
      - If protocol is udp/tcp, keep as udp/tcp
      - If wireguardPublicKey exists, add wireguard (do NOT stop processing)
    """
    out: Set[str] = set()

    # Add wireguard if key exists, but DO NOT return early
    wg_key = entry.get("wireguardPublicKey")
    if isinstance(wg_key, str) and wg_key.strip():
        out.add("wireguard")

    proto = entry.get("protocol")
    if isinstance(proto, str):
        s = proto.strip().lower()
        if s in {"udp", "tcp"}:
            out.add(s)
        elif "openvpn" in s:
            out.add("openvpn")
        else:
            # keep unknown protocol strings if they exist
            if s:
                out.add(s)

    return out


def host_to_region_json(hostname: str) -> Optional[str]:
    """
    Examples:
      ae.lazerpenguin.com               -> AE.json
      us-chicago-tier2.lazerpenguin.com -> US.json  (first 2 chars of first label)
    """
    if not hostname or not isinstance(hostname, str):
        return None
    first_label = hostname.split(".", 1)[0].strip()
    if not first_label:
        return None
    if len(first_label) >= 2:
        # Always: first 2 chars are country code style for this dataset (ae, us, sg, etc.)
        cc = first_label[:2].upper()
        return f"{cc}.json"
    return None


def build_ip_to_host_map_from_logs(log_dir: Path) -> Dict[str, str]:
    """
    Scan logs ONCE and map each seen IP to the currently active nslookup hostname.
    Works for both:
      - 'Address: <ip>'
      - '[...] Resolved IP: <ip>'
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
                    m_ip = IP_RE.search(line)
                    if m_ip:
                        ip = m_ip.group(1)
                        # keep first mapping (stable); switch to overwrite if you want "latest"
                        ip_to_host.setdefault(ip, current_host)
        except Exception:
            continue

    return ip_to_host


def load_region_json(region_json: Path) -> Tuple[Set[str], bool]:
    """
    Return:
      - region_protocols: union of protocol labels across ALL vpns[] in this region
      - has_ipsec flag
    """
    data = load_json(region_json)
    if not data:
        return set(), False

    has_ipsec = isinstance(data.get("ipsec"), str) and bool(data.get("ipsec").strip())

    region_prots: Set[str] = set()
    vpns = data.get("vpns", [])
    if isinstance(vpns, list):
        for entry in vpns:
            if not isinstance(entry, dict):
                continue
            region_prots.update(infer_protocols(entry))


    return region_prots, has_ipsec



def process_one_date(dir_name: str, rows: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str, str]]]:
    """
    rows = [(date_str, ip), ...] for a single dir_name.
    Returns (dir_name, output_rows) where output_rows are (date_str, ip, protocols_csv).
    """
    out_rows: List[Tuple[str, str, str]] = []
    date_dir = BASE_DIR / dir_name
    if not date_dir.is_dir():
        for date_str, ip in rows:
            out_rows.append((date_str, ip, ""))
        return dir_name, out_rows

    ip_to_host = build_ip_to_host_map_from_logs(date_dir / LOG_DIRNAME)

    # Cache only region files needed in this date
    region_cache: Dict[str, Tuple[Set[str], bool]] = {}

    for date_str, ip in rows:
        host = ip_to_host.get(ip)
        if not host:
            out_rows.append((date_str, ip, ""))
            continue

        region_fname = host_to_region_json(host)
        if not region_fname:
            out_rows.append((date_str, ip, ""))
            continue

        if region_fname not in region_cache:
            region_json = date_dir / REGIONS_DIRNAME / region_fname
            region_cache[region_fname] = load_region_json(region_json)

        region_prots, has_ipsec = region_cache[region_fname]
        prots = set(region_prots)
        if has_ipsec:
            prots.add("ipsec")


        out_rows.append((date_str, ip, ",".join(sorted(prots))))

    return dir_name, out_rows


def main() -> None:
    if not BASE_DIR.is_dir():
        raise SystemExit(f"Base dir not found: {BASE_DIR.resolve()}")
    if not IN_CSV.exists():
        raise SystemExit(f"Input CSV not found: {IN_CSV.resolve()}")

    # Group input rows by date directory
    by_dir: Dict[str, List[Tuple[str, str]]] = {}
    bad_date_rows: List[Tuple[str, str]] = []

    with IN_CSV.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.reader(fin)
        next(reader, None)  # skip first line
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

        # write bad-date rows first
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