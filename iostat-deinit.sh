#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 \"test directory\""
    exit 0
fi
test_dir="$1"

#init iostat
if [ "$(which iostat 2>/dev/null)" != "" ]; then
    kill $( cat "$test_dir/iostat.pid")
    rm -f "$test_dir/iostat.pid" > /dev/null
    #for some reasons iostat output contains sometimes null bytes.
    sed -i 's/\x00//g' "$test_dir/iostat"
fi
