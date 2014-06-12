#!/bin/bash
num_blocks=$(echo "1024 * $size" | bc)
echo $num_blocks
cat /dev/zero | nc -l 127.0.0.1 1337 > /dev/null&
sleep 0.1
dd if=/dev/urandom bs=1024 count=102400 | nc 127.0.0.1 1337 > /dev/null
