#!/bin/bash

#This has to be run as root

#parsing arguments
if [ $# -ne 1 ]; then
	echo $#
	echo "Usage: $0 \"test directory\""
	exit 0
fi
test_dir="$1"

if [ "$(which opcontrol 2>/dev/null)" != "" ]; then
	echo "starting oprofile"

	rm -rf "$test_dir/oprofile_data/" &>/dev/null
	opcontrol --reset
	opcontrol --deinit
	modprobe oprofile timer=1
	echo 0 > /proc/sys/kernel/nmi_watchdog
	opcontrol --separate=cpu #--separate=none

	vmlinux="$( cat "$test_dir/wrstat.config" | grep "oprofile_vmlinux" | cut -d " "  -f 2-)"
	if [ "$vmlinux" == "" ]
	then
		opcontrol --start --no-vmlinux --session-dir="$test_dir/oprofile_data/"
	else
		opcontrol --start --vmlinux="$vmlinux" --session-dir="$test_dir/oprofile_data/"
	fi
fi
