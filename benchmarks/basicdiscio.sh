#!/bin/bash
dd bs=1M count=256 if=/dev/zero of=/tmp/test
dd bs=1M count=256 if=/tmp/test of=/dev/null
rm /tmp/test
