#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
    echo $#
    echo "Usage: $0 \"test directory\""
    exit 0
fi
test_dir="$1"

#saving blocksizes
rm "$test_dir/blocksizes" &>/dev/null
for DEVICE in $(ls /sys/block/)
do
    BLCKSIZE=$( cat "/sys/block/$DEVICE/queue/physical_block_size")
    echo $DEVICE $BLCKSIZE >> "$test_dir/blocksizes"
done
