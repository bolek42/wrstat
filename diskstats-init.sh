#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
    echo $#
    echo "Usage: $0 \"test directory\""
    exit 0
fi
test_dir="$1"

#saving sectorsizes
rm "$test_dir/sectorsizes" &>/dev/null
for DEVICE in $(ls /sys/block/)
do
    SECSIZE=$( cat "/sys/block/$DEVICE/queue/hw_sector_size")
    echo $DEVICE $SECSIZE >> "$test_dir/sectorsizes"
done
