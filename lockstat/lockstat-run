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

test_dir="$1"
cmd=${@:2:$#}

mkdir -p "$test_dir"
if [ ! -d "$test_dir" ]; then
	echo "ERROR: failed to created $test_dir directory."
	exit 0
fi

echo "$cmd" > "$test_dir/cmd"

echo "clearing lockstat"
sudo "echo 0 > /proc/lock_stat"


##############
begin_t=`date +%H-%M-%S`

#command line
echo eval $cmd
eval $cmd $i &> "$test_dir/user_output"

end_t=`date +%H-%M-%S`
##############

sudo cat /proc/lock_stat > "$test_dir/lock_stat"


