#!/bin/bash

#parsing arguments
if [ $# -ne 2 ]; then
	echo $#
	echo "Usage: $0 \"test directory\" intervall"
	exit 0
fi
test_dir="$1"
intervall=$2

#init Oprofile
if [ "$(which iostat 2>/dev/null)" != "" ]; then
	iostst -d $intervall > "$test_dir/ios_tat"&
	echo $! > "$test_dir/ios_tat.pid"
fi
