#!/bin/bash

#parsing arguments
if [ $# -ne 2 ]; then
	echo "Usage: $0 \"test directory\""
	exit 0
fi
test_dir="$1"
intervall="$1"

#init Oprofile
if [ "$(which iostat 2>/dev/null)" != "" ]; then
	iostst -d $intervall > "$test_dir/iostat"&
	echo $! > "$test_dir/iostat.pid"
fi
