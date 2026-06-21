#!/usr/bin/env bash
#set -euo pipefail

[[ "${1:-}" == "-d" ]] && DEBUG_FLAG=1 || DEBUG_FLAG=0

POLAR_MAC="24:AC:AC:14:D4:93"
PMD_CONTROL_UUID="fb005c81-02e7-f387-1cad-8acd2d8df0c8"
PMD_DATA_UUID="fb005c82-02e7-f387-1cad-8acd2d8df0c8"

REGEX_FULL_LINE="([a-f0-9]{2} ){16}"
REGEX_LAST_LINE="([a-f0-9]{2} ){5}"

SAMPLE_RATE=0.007692307692307693

declare -A cmd_2_response=(
    ["menu gatt"]="*Run script*"
    ["select-attribute $PMD_DATA_UUID"]="*/service002d/char0031*"
    ["notify on"]="*Notify started*"
    ["select-attribute $PMD_CONTROL_UUID"]="*/service002d/char002e*"
    ["write '0x01 0x00'"]="*f0 01 00 00 00 00 01 82 00 01 01 0e 00*"
    ["write '0x02 0x00 0x00 0x01 0x82 0x00 0x01 0x01 0x0e 0x00'"]="*f0 02 00 00 00 00*"
    ["notify off"]="*Notify stopped*"       
    ["back"]="*Run script*"  
)

order_start=(
    "menu gatt"                 
    "select-attribute $PMD_CONTROL_UUID"
    "notify on"
    "select-attribute $PMD_DATA_UUID"
    "notify on"
    "select-attribute $PMD_CONTROL_UUID"
    "notify on"
    "write '0x01 0x00'"
    "write '0x02 0x00 0x00 0x01 0x82 0x00 0x01 0x01 0x0e 0x00'"
    "select-attribute $PMD_DATA_UUID"
)

order_stop=(
    "notify off"
    "back"
)

_reverse_array() {
    local arr=( "$@" )
    local reversed=()
    local length="${#arr[@]}"

    for (( i=(length - 1); i >= 0; i-- ));
    do
	reversed+=( "${arr[$i]}" )
    done
    
    echo "${reversed[@]}"
}


_concat() {
    local arr=( "$@" )
    echo "$(IFS=; echo "${arr[*]}")"
}


_dec_to_s24bit() {
    local dec="$1"
    local s24bit=""
    
    if (( dec & 16#800000 ));then
	s24bit=$(( -(( ~dec & 16#ffffff ) + 1) ))
    else
	s24bit="$dec"
    fi
    
    echo "$s24bit"
}

_parse_ecg_signal() {
    local packet_raw=( "$@" )
    local length="${#packet_raw[@]}"
    
    local ecg_values=()
    # loop drops last packet if incomplete
    for (( i=0; i < (length - 2) ; i+=3 ));
    do
	slice=( "${packet_raw[@]:i:3}" )
	read -r -a slice_big_endian <<< "$(_reverse_array "${slice[@]}")"
	hex_str="$(_concat "${slice_big_endian[@]}")"
	dec=$(( 16#$hex_str ))
	value="$(_dec_to_s24bit "$dec")"	    
	ecg_values+=( "$(( -1 * value ))" )
    done

    echo "${ecg_values[@]}"
}

_send_and_validate_cmd() {
    local cmd="$1"
    local expected="$2"
    local time_out="$3"
    local line
    local start
    
    start="$(date +%s)"
    
    echo "$cmd" >&"${BLUETOOTHCTL[1]}"
    (( DEBUG_FLAG )) && echo "[Send]: $cmd"
	
    while read -r -t 1 line <&"${BLUETOOTHCTL[0]}";
    do
	(( DEBUG_FLAG )) && echo "[bluetootctl] $line"
	[[ $line == *"$expected"* ]] && return 0
	[[ $line == *"Invalid"* || $line == *"Failed"* ]] && return 1

	    
	if (( $(date +%s) - start >= time_out )); then
	    if (( DEBUG_FLAG )); then
	    	echo "[Time Out] No response from bluetoothctl in ${time_out}s."
	    fi  	  
	    return 1
	fi
    done
}

connect() {
    _send_and_validate_cmd "connect $POLAR_MAC" "[CHG] Device*ServicesResolved: yes" 5
}


start_advertising() {
    for key in "${order_start[@]}"; do 
	_send_and_validate_cmd "$key" "${cmd_2_response[$key]}" 5 || return 1
	if (( DEBUG_FLAG )); then
	    echo "[SUCCESS: $key]"
	fi
    done
}

stop_advertising() {
    # sends stop cmds to bluetoothctl
    for key in "${order_stop[@]}"; do 
	_send_and_validate_cmd "$key" "${cmd_2_response[$key]}" 5 || true
	if (( DEBUG_FLAG )); then
	    echo "[SUCCESS: $key]"
	fi
    done
    return 0
}

clean_up() {
    stop_advertising
    
    echo "disconnect $POLAR_MAC" >&"${BLUETOOTHCTL[1]}"
    echo "exit" >&"${BLUETOOTHCTL[1]}"

    kill "${BLUETOOTHCTL_PID}" 2>/dev/null
    exit 0
}

(( DEBUG_FLAG )) && echo "[--- DEBUG MODE ---]"

coproc BLUETOOTHCTL { stdbuf -oL -eL bluetoothctl; }

sleep 1

trap "clean_up" SIGINT SIGTERM EXIT

connect

start_advertising


batch=()

while read -r line <& "${BLUETOOTHCTL[0]}"; do 
    if [[ "$line" =~ $REGEX_FULL_LINE ]]; then
	IFS=$' ' read -r -a regex_array <<< "${BASH_REMATCH[0]}"
	batch+=( "${regex_array[@]}")
	
    elif [[ "$line" =~ $REGEX_LAST_LINE ]]; then
	IFS=$' ' read -r -a regex_array <<< "${BASH_REMATCH[0]}"
	batch+=( "${regex_array[@]}")    # -> batch complete
	
	## skipping measurement type, timestamp & frame type: data[0:9] 
        read -r -a parsed <<< "$(_parse_ecg_signal "${batch[@]:10}")"
	
	echo "${parsed[@]}" >&1
	
	batch=()
    fi
done
