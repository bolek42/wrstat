#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 \"test directory\""
    exit 0
fi
test_dir="$1"

#init Oprofile
if [ "$(which iostat 2>/dev/null)" != "" ]; then
    intervall="$( cat "$test_dir/wrstat.config" | grep "intervall" | cut -d " "  -f 2-)"
    iostat -d $intervall > "$test_dir/iostat"&
    echo $! > "$test_dir/iostat.pid"
fi
