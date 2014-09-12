#!/bin/bash

#This has to be run as root

#parsing arguments
if [ $# -ne 1 ]; then
    echo $#
    echo "Usage: $0 \"test directory\""
    exit 0
fi
test_dir="$1"


#deinit oprofile
if [ "$(which opcontrol 2>/dev/null)" != "" ]; then
    echo "deinit oprofile"
    kernel_mod="$( cat "$test_dir/wrstat.config" | grep "oprofile_kernel_mod" | cut -d " "  -f 2-)"
    opcontrol --stop
    opcontrol --dump
    opcontrol --shutdown
    #opreport --session-dir="$test_dir/oprofile_data/" -p $kernel_mod -l > "$test_dir/oprof_results"
    opreport --session-dir="$test_dir/oprofile_data/" -l > "$test_dir/samples/oprofile"
fi
