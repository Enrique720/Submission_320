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

if python3 "$script_dir/get_servers.py" "$out_dir"
then
  echo "Successfully fetched servers and saved to $out_dir"
  nohup bash "$script_dir/../../utils/findServerIP.sh" "$out_dir/region_prefix.txt" "$out_dir/master_ip_list.txt" > "$out_dir/findServerIP.log" 2>&1 &
else
  # find regions prefix file 
  last_file=$(find "$folder" -type f -name "region_prefix.txt" | sort | tail -n 1)
  nohup bash "$script_dir/../../utils/findServerIP.sh" "$last_file" "$out_dir/master_ip_list.txt" > "$out_dir/findServerIP.log" 2>&1 &
fi
