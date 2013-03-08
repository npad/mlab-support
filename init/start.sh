#!/bin/bash

set -e 
set -x
source /etc/mlab/slice-functions
source $SLICEHOME/conf/config.sh
source $SLICEHOME/.bash_profile

USER=root
PIDFILE=/var/run/npad.pid
DIAG_SERVER_OPTS="-d -u $USER -p $PIDFILE"
DIAG_SERVER_DAEMON=$SLICEHOME/build/DiagServer.py

if [ -f $PIDFILE ]; then
	pid=`cat $PIDFILE`
	if [ "`ps -p $pid -o comm=`" = "DiagServer.py" ]; then
		echo "NPAD server already running, not starting."
		exit 1
	fi
fi
${DIAG_SERVER_DAEMON} ${DIAG_SERVER_OPTS}
echo "NPAD server started."
$SLICEHOME/build/redisplay.py -daemon $SLICEHOME/VAR/www/ServerData $RSYNCDIR_NPAD $MYNODE &
sudo -i -u $SLICENAME $SLICEHOME/build/bin/doside
