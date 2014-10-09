#!/bin/bash

#This has to be run as root

#parsing arguments
if [ $# -ne 1 ]; then
    echo $#
    echo "Usage: $0 \"test directory\""
    exit 0
fi
test_dir="$1"

#read config file
use_operf="$( cat "$test_dir/wrstat.config" | grep "oprofile_use_operf" | cut -d " "  -f 2-)"
use_operf=${use_operf,,}
vmlinux="$( cat "$test_dir/wrstat.config" | grep "oprofile_vmlinux" | cut -d " "  -f 2-)"
event="$( cat "$test_dir/wrstat.config" | grep "oprofile_event" | cut -d " "  -f 2-)"

rm -rf "$test_dir/oprofile_data/" &>/dev/null
mkdir "$test_dir/oprofile_data/"

#check if we should use operf or opcontrol (deprecated)
if [ $use_operf == "true" ]; then
    if [ "$(which operf 2>/dev/null)" != "" ]; then
        #starting operf
        if [ "$vmlinux" == "" ];then
            operf --system-wide --separate-cpu --session-dir="$test_dir/oprofile_data/" --events="$event"&
        else
            ln -sf "$vmlinux" "$test_dir/vmlinux"
            operf --system-wide --separate-cpu --vmlinux="$test_dir/vmlinux" --session-dir="$test_dir/oprofile_data/" --events="$event"&
        fi
        echo $! > "$test_dir/operf.pid"
    fi
#opcontrol
else
    if [ "$(which opcontrol 2>/dev/null)" != "" ]; then
        echo "starting oprofile"

        opcontrol --reset
        opcontrol --deinit
#        modprobe oprofile timer=1
        echo 0 > /proc/sys/kernel/nmi_watchdog
        opcontrol --separate=cpu
        opcontrol --event="$event"

        if [ "$vmlinux" == "" ];then
            opcontrol --start --no-vmlinux --session-dir="$test_dir/oprofile_data/"
        else
            ln -sf "$vmlinux" "$test_dir/vmlinux"
            opcontrol --start --vmlinux="$test_dir/vmlinux" --session-dir="$test_dir/oprofile_data/"
        fi
    fi
fi
