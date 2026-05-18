#!/bin/bash

POLAR_MAC="24:AC:AC:14:D4:93"
PMD_CONTROL_UUID="fb005c81-02e7-f387-1cad-8acd2d8df0c8"
PMD_DATA_UUID="fb005c82-02e7-f387-1cad-8acd2d8df0c8"

start_stream=(
    "menu gatt"                 
    "select-attribute $PMD_DATA_UUID"
    "notify on"
    "select-attribute $PMD_CONTROL_UUID"
    "notify on"
    "write '0x01 0x00'"
    "write '0x02 0x00 0x00 0x01 0x82 0x00 0x01 0x01 0x0e 0x00'"
    "select-attribute $PMD_DATA_UUID"
)

stop_stream=(
    "select-attribute $PMD_DATA_UUID"
    "notify off"
    "disconnect"
    "exit"
)

cleanup() {
    local delay="$1"
    echo -e "\n🛑 Stopping stream and disconnecting cleanly..."
    for cmd in "${stop_stream[@]}"; do
	to_coproc "$cmd" "$delay"
    done

    echo "👋 Interface released successfully."
    exit 0
}


to_coproc() {
    local cmd="$1"
    local delay="$2"
    # echo "$cmd" >& "${BLUETOOTHCTL[1]}";
    sleep "$delay";
}


############################################################
#  MAIN
############################################################
echo "❤️ Initializing Polar H10 RAW ECG Stream via Bash coproc..."
echo "Press Ctrl+C at any time to exit safely."

coproc BLUETOOTHCTL { bluetoothctl; }

trap "cleanup 2" INT TERM

to_coproc "connect $POLAR_MAC" 10

for cmd in "${start_stream[@]}"; do
    to_coproc "$cmd" 3
done

echo "📡 Streaming active. Listening for incoming data..."

while read -r line <& "${BLUETOOTHCTL[0]}"; do
    echo "$line" | sed -E -e '/^ *$/d' -e '/Value:/d' -e 's/  +([^ ]*)$//';
done
