#!/bin/bash
cat /dev/urandom | nc -l 127.0.0.1 1337 > /dev/null&
sleep 0.1
dd if=/dev/zero bs=1M count=1024 | nc 127.0.0.1 1337 > /dev/null
sleep 3

