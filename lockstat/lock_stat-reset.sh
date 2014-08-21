#!/bin/bash

echo "reset /proc/lock_stat"
sudo su -m -c "echo 0 > /proc/lock_stat"
