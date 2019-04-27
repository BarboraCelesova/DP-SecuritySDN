#!/usr/bin/python

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import time
import datetime
from datetime import datetime as dt
import thread
import random

def WaitTillEndOfSec(sec):
    t = datetime.datetime.utcnow()
    sleeptime = sec - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

def BaseTraffic(host, startIP, endIP, endIter, sec):
    dateTimeObj = dt.now()
    # get the time object from datetime object
    timeObj = dateTimeObj.time()
    dept_time = timeObj.strftime("%H:%M:%S.%f")

    print '++ TRAFFIC', dept_time, startIP, endIP

    for i in range(startIP, endIP):
        for j in range(0, endIter):
            host[i].cmd('mausezahn h' + str(i) + '-eth0 -c ' + str(sec) + ' -d 1s -b aa:bb:cc:dd:ee:ff -B 10.0.0.100 -t udp &')

def CreateTopology():
    net = Mininet(controller=RemoteController, link=TCLink, switch=OVSKernelSwitch)

    print 'Creating nodes...'
    h = {}
    for i in range(1, 101):
        h[i] = net.addHost('h' + str(i), mac='00:00:00:00:00:' + str(i), ip='10.0.0.' + str(i) + '/24')

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    print 'Creating links...'
    for i in range(1, 51):
        net.addLink(h[i], s1, bw=100)

    for i in range(51, 101):
        net.addLink(h[i], s2, bw=100)

    net.addLink(s1, s2, bw=100)

    print 'Starting network...'
    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])

    print 'Verifying connectivity...'
    #loss = net.pingAll()

    host = {}

    print '*** Mausezahn flood...'
    for i in range(1, 101):
        host[i] = net.getNodeByName('h' + str(i))

    # Wait until end of second
    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)
    #


    # NoNAttack traffic for 25 users for each 2 seconds
    x = 1
    for count in range(0, 25):
        BaseTraffic(host, x, x + 25, 2, 2)
        x += 25

        if x >= 54:
            x = 1
        WaitTillEndOfSec(2)
    # ------
    #
    # # RANDOM
    # for p in range(0, 50):
    #     for j in range(0, 50):
    #         x = random.randint(1, 79)
    #         BaseTraffic(host, x, x + 1, 1, 1)
    #     WaitTillEndOfSec(1)

    #  NoNAttack traffic 10 and 5 users for each 5 seconds
    # x = 1
    # for count in range(0, 10):
    #
    #     BaseTraffic(host, x, x + 10, 3, 5)
    #     BaseTraffic(host, x + 10, x + 15, 4, 5)
    #     x += 15
    #
    #     if x >= 64:
    #         x = 1
    #
    #     WaitTillEndOfSec(5)

    # x = 1
    # for count in range(0, 16):
    #
    #     BaseTraffic(host, x, x + 10, 3, 3)
    #     BaseTraffic(host, x + 10, x + 15, 4, 3)
    #     x += 15
    #
    #     if x >= 64:
    #         x = 1
    #
    #     WaitTillEndOfSec(3)
    #
    # BaseTraffic(host, 65, 75, 3, 2)
    # BaseTraffic(host, 75, 80, 4, 2)

    # x = 1
    # for count in range(0, 16):
    #     BaseTraffic(host, x, x + 16, 2, 3)
    #     BaseTraffic(host, x + 16, x + 22, 3, 3)
    #     x += 22
    #
    #     if x >= 58:
    #         x = 1
    #
    #     WaitTillEndOfSec(3)
    #
    # BaseTraffic(host, 55, 80, 2, 2)

    print 'Running CLI...'
    CLI(net)

    print 'Stopping network...'
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    CreateTopology()
