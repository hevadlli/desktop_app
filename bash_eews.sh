#!/bin/bash

# Function to handle cleanup before exiting
cleanup() {
    pids=$(ps aux | grep -E "python3 eews_part[1-5].py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        kill -9 $pids > /dev/null 2>&1
    fi
    echo ""
    echo "Program EEWS berhasil dihentikan."
    exit 0
}

# Set trap to call cleanup function on SIGINT
trap cleanup SIGINT

echo "Program EEWS berjalan di background..."
echo "Tekan CTRL+C untuk menghentikan program"

while true; do
    # Menutup program Python yang sedang berjalan
    pids=$(ps aux | grep -E "python3 eews_part[1-5].py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        kill -9 $pids > /dev/null 2>&1
    fi

    # Start the Python scripts
    nohup python3 eews_part1.py > log/eews_part1.log 2>&1 &
    nohup python3 eews_part2.py > log/eews_part2.log 2>&1 &
    nohup python3 eews_part3.py > log/eews_part3.log 2>&1 &
    nohup python3 eews_part4.py > log/eews_part4.log 2>&1 &
    nohup python3 eews_part5.py > log/eews_part5.log 2>&1 &
    
    sleep 3600
done
