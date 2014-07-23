#!/bin/bash

#$1=test name
#$2..$#= cmd

vmlinux="/home/hammel/linux/vmlinux"
procfiles="/proc/stat /proc/lock_stat /proc/diskstats "
kernel_mod="/home/hammel/linux/"

#get the location of the current script
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
tool_path="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

#parsing arguments
if [ $# -lt 2 ]; then
	echo "Usage: $0 \"test directory\" prog [arg1] [arg2] ..."
	exit 0
fi

if [ "$(which $2 2>/dev/null)" = "" ]; then
	echo "ERROR: \"$2\" comand or file not found"
	exit 0
fi

cmd=${@:2:$#}
test_dir="$1"

mkdir -p "$test_dir"
if [ ! -d "$test_dir" ]; then
	echo "ERROR: failed to created $test_dir directory."
	exit 0
fi

echo "$cmd" > "$test_dir/cmd"

#init lockstat
echo "clearing lockstat"
sudo su -m -c "echo 0 > /proc/lock_stat"

#init Oprofile
if [ "$(which opcontrol 2>/dev/null)" = "" ]; then
	echo "starting oprofile"
	sudo opcontrol --reset
	sudo opcontrol --deinit
	sudo modprobe oprofile timer=1
	sudo su -m -c "echo 0 > /proc/sys/kernel/nmi_watchdog"
	sudo opcontrol --separate=cpu
fi

#if [ $oprof_mode = "separate" ]; then
#else
#	sudo opcontrol --separate=none
#fi
rm -rf "$test_dir/oprofile_data/"
sudo opcontrol --start --vmlinux="$vmlinux" --session-dir="$test_dir/oprofile_data/"

#sampling deamon for /proc files
sample_dir="$test_dir/samples"
mkdir -p "$sample_dir"
rm -f "$sample_dir"/*
sudo python "$tool_path/lockstat-sampling-deamon.py" "$sample_dir" $procfiles&
sampling_deamon_pid=$!

##############
begin_t=`date +%H-%M-%S`

#command line
echo eval $cmd
eval $cmd $i &> "$test_dir/user_output"

end_t=`date +%H-%M-%S`
##############

#deinit sampling deamon
echo "killing sampling deamon..."
sudo kill -SIGTERM $sampling_deamon_pid
wait $sampling_deamon_pid

#deinit oprofile
if [ "$(which opcontrol 2>/dev/null)" = "" ]; then
	sudo opcontrol --stop
	sudo opcontrol --dump
	sudo opcontrol --shutdown
	opreport --session-dir="$test_dir/oprofile_data/" -p $kernel_mod -l > "$test_dir/oprof_results"
fi

user=$USER
group=$(id -gn)
sudo chown -R $user:$group "$test_dir"
find "$test_dir" -type d -exec chmod 755 {} \;
find "$test_dir" -type f -exec chmod 644 {} \;

sudo cat /proc/lock_stat > "$test_dir/lock_stat"

python "$tool_path/lockstat-parser.py" "$sample_dir" "$test_dir/samples.pickle"
python "$tool_path/lockstat-graph.py" "$test_dir"
