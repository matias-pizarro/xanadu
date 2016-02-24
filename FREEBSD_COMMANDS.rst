============================
Some useful FreeBSD commands
============================

`sockstat <https://www.freebsd.org/cgi/man.cgi?iostat>`_
========

list open IPv46 sockets: ::

    sockstat -46



`systat <https://www.freebsd.org/cgi/man.cgi?query=systat&apropos=0&sektion=0&manpath=FreeBSD+10.2-RELEASE&arch=default&format=html>`_
======

**display system statistics**

Network connections: ::

    systat -netstat 1

Network traffic going through active interfaces: ::

    systat -ifstat 1

Processor use and disk throughput: ::

    systat -iostat 1

Tx/Rx for one of icmp, icmp6, ip, ip6, tcp (in example): ::

    systat -tcp 1



`iostat <https://www.freebsd.org/cgi/man.cgi?iostat>`_
======

Display up  to 8 devices with the most I/O every second ad infinitum: ::

    iostat -h -n 8 -w 1



`lsof <https://www.freebsd.org/cgi/man.cgi?query=lsof&manpath=FreeBSD+10.2-RELEASE+and+Ports&format=html>`_
====

To list all open    Internet, x.25 (HP-UX), and UNIX domain files, use: ::

    lsof -i -U

To find the process that has /var/run/log open, use: ::

    lsof /var/run/log

To send a SIGHUP to the processes that have /var/run/log open, use: ::

    kill -HUP `lsof -t /u/abe/bar`



`pf <https://www.freebsd.org/cgi/man.cgi?query=pfctl&sektion=8&apropos=0&manpath=FreeBSD+10.2-RELEASE>`_
==

show pf info: ::

    pfctl -s info

enable pf: ::

    pfctl -e

disable pf (don't!): ::

    pfctl -d

parse and check pf rules sanity: ::

    pfctl -nf /etc/pf.conf

load pf rules: ::

    pfctl -f /etc/pf.conf

load pf rules and flush everything: ::

    pfctl -F all -f /etc/pf.conf

load pf rules and flush nat and rules: ::

    pfctl -F nat -F rules -f /etc/pf.conf

live capture of pf activity: ::

    tcpdump -netttti pflog0
