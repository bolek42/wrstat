#!/bin/bash
dd bs=1M count=1024 if=/dev/zero of=/tmp/test
sleep 3
dd bs=1M count=1024 if=/tmp/test of=/dev/null
rm /tmp/test
