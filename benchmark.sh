#!/bin/bash
cat /dev/urandom | nc -l 127.0.0.1 1337 > /dev/null&
sleep 0.1
dd if=/dev/zero bs=1024 count=1024000 | nc 127.0.0.1 1337 > /dev/null
sleep 3
