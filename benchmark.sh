#!/bin/bash
num_blocks=$(echo "1024 * $size" | bc)
echo $num_blocks
cat /dev/zero | nc -l 127.0.0.1 1337 > /dev/null&
sleep 0.1
sudo dd if=/dev/sda bs=1024 count=1024000 | nc 127.0.0.1 1337 > /dev/null
