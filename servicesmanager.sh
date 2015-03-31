#!/bin/bash   

quit=0
while getopts "qs:" opt; do
  case $opt in
    q)
      quit=1
      ;;
    s)
      service=$OPTARG
      ;;
  esac
done    
if [ -z $service ] ; then 
	echo "-s service is needed"
	exit 1
elif [ $service = "DBSync" ] ; then
	if [ $quit -eq 0 ] ; then
		setsid ~/mongosync -h 54.187.240.68:27017 -u root -p 910813gyb --to 115.156.196.215:27017 -tu root -tp 910813gyb --oplog -s 1369406664,1 >~/dav/sync.log 2>&1 &
		echo "startDBSync"
		exit 0
	else
		kill -9 $(ps aux|awk '/mongosync/{print $1}')
		echo "stopDBSync"
		exit 0
	fi
elif [ $service = "JobManager" ] ; then
	if [ $quit -eq 0 ] ; then
		setsid python ~/dav/rsbackend/jobmanager.py >~/dav/rsbackend/jobmanager.log 2>&1 &
		echo "startJobManager"
		exit 0
	else
		kill -9 $(ps aux|awk '/jobmanager/{print $1}')
		echo "stopJobManager"
		exit 0
	fi
fi 


