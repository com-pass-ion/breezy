#!/bin/bash

[[ "$1" == "-d" ]] && DEBUG_FLAG=1 || DEBUG_FLAG=0

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
    "back"
    "disconnect"
    "exit"
)

cleanup() {
    local delay="$1"
    
    if (( DEBUG_FLAG ));then
	echo -e "\n🛑 Stopping stream and disconnecting cleanly..."
    fi
    for cmd in "${stop_stream[@]}"; do
	to_coproc "$cmd" "$delay"
    done
    if (( DEBUG_FLAG ));then
	echo "👋 Interface released successfully."
    fi
    
    exit 0
}


to_coproc() {
    local cmd="$1"
    local delay="$2"

    if (( DEBUG_FLAG ));then
	echo "[Send]: $cmd"
    fi
    
    echo "$cmd" >& "${BLUETOOTHCTL[1]}"
    
    sleep "$delay";
}

REGEX_FULL_LINE="([a-f0-9]{2} ){15}[a-f0-9]{2}"
REGEX_LAST_LINE="([a-f0-9]{2} ){3}[a-f0-9]{2}"

############################################################
#  MAIN
############################################################
if (( DEBUG_FLAG ));then
    echo "[--- DEBUG MODE ---]"
    echo "❤️ Initializing Polar H10 RAW ECG Stream via Bash coproc..."
    echo "Press Ctrl+C at any time to exit safely."
fi

### REDIRECTION FOR DEBUG-MODE
coproc BLUETOOTHCTL { bluetoothctl; }
sleep 1

trap "cleanup 2" INT TERM

to_coproc "connect $POLAR_MAC" 3

for cmd in "${start_stream[@]}"; do
    to_coproc "$cmd" 2
done

if (( DEBUG_FLAG ));then
    echo "📡 Streaming active. Listening for incoming data..."
fi


packet_array=()

while read -r line <& "${BLUETOOTHCTL[0]}"; do
    if [[ "$line" =~ $REGEX_FULL_LINE ]]; then
	IFS=$' ' read -r -a line_array <<< "${BASH_REMATCH[0]}"
	packet_array+=( "${line_array[@]}")
	
    elif [[ "$line" =~ $REGEX_LAST_LINE ]]; then
	IFS=$' ' read -r -a line_array <<< "${BASH_REMATCH[0]}"
	packet_array+=( "${line_array[@]}")

	### PARSING LOGIC
	echo "${packet_array[@]}"

	packet_array=()
    fi    
done
