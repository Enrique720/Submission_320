#!/bin/bash

if [ -z "$1" ]
  then
    echo "Usage: $0 <folder>"
    exit 1
fi

date=$(date +'%m_%d_%Y')

folder=$1

out_dir=$folder/$date

mkdir -p $out_dir

script_dir=$(dirname "$0")

python3 "$script_dir/get_servers.py" "$out_dir"

nohup bash "$script_dir/../../utils/findServerIP.sh" "$out_dir/server_names.txt" "$out_dir/master_ip_list.txt" > "$out_dir/findServerIP.log" 2>&1 &