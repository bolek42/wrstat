#!/bin/bash

#This has to be run as root

echo "reset /proc/lock_stat"
echo 0 > /proc/lock_stat
