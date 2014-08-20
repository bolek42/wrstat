#!/bin/bash

#parsing arguments
if [ $# -ne 1 ]; then
	echo $#
	echo "Usage: $0 \"test directory\""
	exit 0
fi
test_dir="$1"

vmlinux="$( cat "$test_dir/lockstat.config" | grep "vmlinux" | cut -d " "  -f 2-)"

#init Oprofile
if [ "$(which opcontrol 2>/dev/null)" != "" ]; then
	echo "starting oprofile"
	sudo opcontrol --reset
	sudo opcontrol --deinit
	sudo modprobe oprofile timer=1
	sudo su -m -c "echo 0 > /proc/sys/kernel/nmi_watchdog"
	sudo opcontrol --separate=cpu
#	sudo opcontrol --separate=none #separate

	rm -rf "$test_dir/oprofile_data/"

	if [ "$vmlinux" == "" ]
	then
		sudo opcontrol --start --no-vmlinux --session-dir="$test_dir/oprofile_data/"
	else
		sudo opcontrol --start --vmlinux="$vmlinux" --session-dir="$test_dir/oprofile_data/"
	fi

fi
