#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
	echo $#
	echo "Usage: $0 \"test directory\""
	exit 0
fi
test_dir="$1"

#init Oprofile
if [ "$(which iostat 2>/dev/null)" != "" ]; then
	kill $( "$test_dir/ios_tat.pid")
fi
