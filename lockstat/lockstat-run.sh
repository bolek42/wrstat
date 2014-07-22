#!/bin/bash

#$1=test name
#$2..$#= cmd

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

echo "clearing lockstat"
sudo su -m -c "echo 0 > /proc/lock_stat"

procfiles="/proc/stat /proc/lockstat /proc/diskstats "
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

user=$USER
sudo chown $user "$sample_dir"/*
chmod 660 "$sample_dir"/*

end_t=`date +%H-%M-%S`
##############

sudo kill -SIGTERM $sampling_deamon_pid

sudo cat /proc/lock_stat > "$test_dir/lock_stat"

python "$tool_path/lockstat-graph.py" "$test_dir"
