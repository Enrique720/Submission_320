#!/bin/bash
if [ -z "$1" ]
  then
    echo "Usage: $0 <folder>"
    exit 1
fi

url=


date=$(date +'%m_%d_%Y')

folder=$1

out_dir=$folder/$date

mkdir -p $out_dir

script_dir=$(dirname "$0")

wget -O $out_dir/servers.json $url

python3 "$script_dir/get_ips.py" $out_dir/servers.json "$out_dir"

nohup bash "$script_dir/../../utils/findServerIP.sh" "$out_dir/connections.txt" "$out_dir/master_ip_list.txt" > "$out_dir/findServerIP.log" 2>&1 &