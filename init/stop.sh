#!/bin/bash

set -e 
set -x
export LD_LIBRARY_PATH=/home/iupui_npad/build/lib/
export PYTHONPATH=/home/iupui_npad/build/lib/python2.6/site-packages/
DIAG_SERVER_DAEMON=/home/iupui_npad/build/DiagServer.py
USER=root
PIDFILE=/var/run/npad.pid
DIAG_SERVER_OPTS="-d -u $USER -p $PIDFILE"

if [ -f $PIDFILE ]; then
	killall redisplay.py || :
	killall exitstats.py || :
	killall tcpdump || : 	
	killall -9 tdump8000.py || : 	# does not respect sigterm
	pid=`cat $PIDFILE`
	if [ "`ps -p $pid -o comm=`" = "DiagServer.py" ]; then
		kill $pid
		rm $PIDFILE
		exit 0
	fi
fi
