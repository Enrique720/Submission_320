#!/bin/bash

SERVER_FILE=$1  # File containing one server name per line
INTERVAL=10                # seconds between lookups
DURATION=3600              # total duration in seconds (1 hour)
ITERATIONS=$((DURATION / INTERVAL))
NEW_IP_TIMEOUT=120         # seconds
MASTER_FILE=$2  # Shared list of new IPs
LOG_DIR=$(dirname "$MASTER_FILE")/logs

# Clear or create master file at the beginning
> "$MASTER_FILE"

# Function to track DNS for a single server
track_server_dns() {
    SERVER_NAME=$1
    mkdir -p "$LOG_DIR"
    LOG_FILE="$LOG_DIR/${SERVER_NAME//./_}_dns_log.txt"

    #LOG_FILE="${SERVER_NAME//./_}_dns_log.txt"

    declare -A ip_counts
    declare -A ip_last_seen

    last_new_ip_time=$(date +%s)

    echo "[$(date)] Starting DNS tracking for $SERVER_NAME"
    echo "Logging every $INTERVAL seconds for $DURATION seconds..." | tee -a "$LOG_FILE"

    for ((i = 1; i <= ITERATIONS; i++)); do
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
        NOW=$(date +%s)

        echo "[$TIMESTAMP] nslookup result for $SERVER_NAME:" >> "$LOG_FILE"
        nslookup "$SERVER_NAME" >> "$LOG_FILE" 2>/dev/null

        IP=$(nslookup "$SERVER_NAME" 2>/dev/null | awk '/^Address: / { print $2 }' | tail -n 1)

        if [ -n "$IP" ]; then
            echo "[$TIMESTAMP] Resolved IP: $IP" >> "$LOG_FILE"

            if [[ -z "${ip_counts[$IP]}" ]]; then
                ip_counts[$IP]=1
                ip_last_seen[$IP]=$NOW
                last_new_ip_time=$NOW
                echo "[$TIMESTAMP] New IP seen: $IP" | tee -a "$LOG_FILE"

                # Add to master list if not already there
                {
                    flock 200
                    if ! grep -qx "$IP" "$MASTER_FILE"; then
                        echo "$IP" >> "$MASTER_FILE"
                        echo "[$TIMESTAMP] Added $IP to master list." >> "$LOG_FILE"
                    fi
                } 200<"$MASTER_FILE"

            else
                ip_counts[$IP]=$(( ${ip_counts[$IP]} + 1 ))
                ip_last_seen[$IP]=$NOW
                echo "[$TIMESTAMP] IP $IP seen again. Count: ${ip_counts[$IP]}" >> "$LOG_FILE"
            fi
        else
            echo "[$TIMESTAMP] Lookup failed or no IP found" >> "$LOG_FILE"
        fi

        all_seen_multiple_times=true
        for count in "${ip_counts[@]}"; do
            if (( count < 2 )); then
                all_seen_multiple_times=false
                break
            fi
        done

        time_since_last_new=$((NOW - last_new_ip_time))
        if $all_seen_multiple_times && (( time_since_last_new >= NEW_IP_TIMEOUT )); then
            echo "[$TIMESTAMP] All IPs seen more than once and no new IP in last $NEW_IP_TIMEOUT seconds." | tee -a "$LOG_FILE"
            break
        fi

        sleep "$INTERVAL"
    done

    echo "[$(date)] Logging complete for $SERVER_NAME" | tee -a "$LOG_FILE"
}

# Check if server file exists
if [ ! -f "$SERVER_FILE" ]; then
    echo "Server file '$SERVER_FILE' not found."
    exit 1
fi

# Read server names from the file and track each in parallel
while IFS= read -r SERVER || [[ -n "$SERVER" ]]; do
    [[ -z "$SERVER" || "$SERVER" =~ ^# ]] && continue  # Skip empty lines or comments
    track_server_dns "$SERVER" &
done < "$SERVER_FILE"

# Wait for all background jobs to finish
wait
echo "All DNS tracking completed."
