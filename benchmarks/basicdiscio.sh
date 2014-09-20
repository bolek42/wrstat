#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
	echo "Usage: $0 \"test directory\""
	exit 0
fi

dd bs=1M count=1k if=/dev/zero of="$1"
sync
dd bs=1M count=1k if="$1" of=/dev/null
rm /tmp/test
