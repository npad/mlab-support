#! /usr/bin/python -u
"""
Take standard NPAD data and redisplay it conformant
the M-Lab data dropbox naming convention.  (Mostly using hard links).

Does not alter the NPAD format data.


"""

import glob
import os.path
import time
import sys
import subprocess

def getIPaddr(prefix):
    """
    Get the IP address of the client, by grocking the .html report.
    """
    addr="Unknown"
    f=open(prefix+".html", "r")
    for l in f:
        w=l.split(" ")
        if w[0] == "Target:":
            addr=w[2].lstrip("(").rstrip(")")
            break
    f.close()
    return(addr)


    """
    Busted (but otherwise more correct) web100 method
    Open a web100 logfile to extract the "RemoteAddr"

    print "Opening", log

    vlog = libweb100.web100_log_open_read(log)
    agent = libweb100.web100_get_log_agent(vlog)
    group = libweb100.web100_get_log_group(vlog)
    conn  = libweb100.web100_get_log_connection(vlog)
    var = libweb100.web100_var_find(group, "RemoteAddr")

    snap  = libweb100.web100_snapshot_alloc(group, conn)
    libweb100.web100_snap_from_log(snap, vlog)
    buf=cast(create_string_buffer(20), cvar.anything) # XXX
    libweb100.web100_snap_read(var, snap, buf)
    val=libweb100.web100_value_to_text(WEB100_TYPE_IP_ADDRESS, buf)
    libweb100.web100_log_close_read(vlog)
    print val
    """

def mkdirs(name):
    """ Fake mkdir -p """
    cp=0
    while True:
        cp=name.find("/",cp+1)
        if cp < 0:
            return
        dirname=name[0:cp]
        try:
            os.mkdir(dirname)
        except OSError, e:
            if e[0] != 17:
                raise e

dfmt="%s/%4s/%2s/%2s/%s/"
def domonth(om, newpath, servname):
    """
    Process all of the files in an old style month dir, computing new
    day dir and names as needed.   We have to maintain bug
    compatability with truncated host names to avoid doubling the
    archive with duplicate data.
    """
    for fl in glob.glob(om+"*.ctrl"):
        # XXX first field separation depends on knowing their lengths.
        # (only the hostname part is unknown)
        oldprefix=fl[:-5]
        tstamp=oldprefix[-19:]
        year=tstamp[0:4]
        month=tstamp[5:7] # XXX no check for wrong dir
        day=tstamp[8:10]
        newdir=dfmt%(newpath, year, month, day, servname)
        if os.path.exists(newdir+"manifest.md5"):
            continue
        time=tstamp[11:]
        hostname=oldprefix[len(om):len(oldprefix)-20]
        badname=oldprefix[len(om)+1:len(oldprefix)-20]
        addr=getIPaddr(oldprefix)  # read the IP addr from a file
        newprefix=newdir+"%sT%sZ_%s_%s"%(year+month+day, time, addr, hostname)
        badprefix=newdir+"%sT%sZ_%s_%s"%(year+month+day, time, addr, badname)
        mkdirs(newprefix)
        for of in glob.glob(oldprefix+"*"):
            suffix=of[len(oldprefix):]
            nf=newprefix+suffix
            bf=badprefix+suffix
            if not os.path.exists(nf) and not os.path.exists(bf):
                os.link(of, nf)

def numdays(m, y):
    "Calculate number of days in each month"
    r=[31,0,31,30,31,30,31,31,30,31,30,31][m-1]
    if not r:
        if y%4 == 0 and y%100 != 0:
            r=29
        else:
            r=28
    return(r)

def redisplay(opath, newpath, servname):
    """
    Traverse a native style NPAD result tree (opath), and generate a
    MLab style result tree.

    This scans month by month in order across the entire native tree.
    To make it scale better with time it skips over any month
    for which the next month (indicated by (nm, ny))already exists.

    Note that the old tree is organized by months, the new tree, by
    days of the month.

    Input paths must be absolute.

    """
    if (opath[0] != "/") or (newpath[0] != "/"):
        print "Arguments must be absolute paths"
        sys.exit(2)
        
    (nowyr, nowmo, nowda, x, x, x, x, x, x) = time.gmtime(time.time()) # starting tstamp
    
    year=2008
    while True:
        year=year+1
        for month in range(1, 13):
            if year > nowyr or (year == nowyr and month > nowmo):
                return
            om="%s/Reports-%04d-%02d/"%(opath, year, month)
            # compute the next month
            ny, nm=year, month+1
            if nm > 12:
                ny, nm = year+1, 1
            mkdirs("%s/%04d/%02d/"%(newpath, year, month))
            if os.path.exists(om) and not os.path.exists("%s/%04d/%02d/"%(newpath, ny, nm)):
                print "Scanning", om
                domonth(om, newpath, servname)
                for day in range(1,numdays(month, year)+1):
                    if year == nowyr and month == nowmo and day >= nowda: # today is not complete
                        return
                    daydir="%s/%4s/%02d/%02d/%s/"%(newpath, year, month, day, servname)
                    mkdirs(daydir)
                    if not os.path.exists(daydir+"manifest.md5"):
                        print "Completing", daydir
                        postproc(daydir)

def postproc(dir):
    """
    Remove all write permissions, compute md5sums, etc
    """
    os.chdir(dir)
    for f in glob.glob(dir+"*"):
        os.chmod(f, 0444)
    subprocess.call("find . -type f | xargs md5sum > ../manifest.tmp", shell=True)
    os.rename("../manifest.tmp", "manifest.md5")
    os.chmod("manifest.md5", 0555)
    os.chmod(dir, 0555)    # And make it immutable 

# main
interval=24*60*60	# Once per day
offset=30*60		# at 00:30:00Z every day (GMT)
argv=sys.argv[:]
if len(argv) < 4:
    print "Usage: %s [-daemon] old_path new_path server_name"%argv[0]
    sys.exit()
if len(argv)==5 and argv[1]=="-daemon":
    del argv[1]
    while True:
	redisplay(argv[1], argv[2], argv[3]) # once at start
        now=time.time()
        nextt=(int(now/interval)+1)*interval+offset
        time.sleep(nextt-now)
        
redisplay(argv[1], argv[2], argv[3])

