#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
	echo "Usage: $0 \"test directory\""
	exit 0
fi
test_dir="$1"

#init iostat
if [ "$(which iostat 2>/dev/null)" != "" ]; then
	kill $( "$test_dir/iostat.pid")
fi
