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

def GrowingTraffic(host, startIP, endIP, endIter, sec):
    dateTimeObj = dt.now()
    # get the time object from datetime object
    timeObj = dateTimeObj.time()
    dept_time = timeObj.strftime("%H:%M:%S.%f")

    print '++ GROWING TRAFFIC', dept_time, startIP, endIP
    for y in range(0, endIter):
        for i in range(startIP, endIP):
            host[i].cmd('mausezahn h' + str(i) + '-eth0 -c ' + str(sec) + ' -d 1s -b aa:bb:cc:dd:ee:ff -B 10.0.0.100 -t udp &')
            sec -= 1
            if sec == 0:
                WaitTillEndOfSec(1)
                return
            WaitTillEndOfSec(1)

def WaveTrafficPlus(host, startIP, endIP, endIter, sec):
    dateTimeObj = dt.now()
    # get the time object from datetime object
    timeObj = dateTimeObj.time()
    dept_time = timeObj.strftime("%H:%M:%S.%f")

    print '++ WAVE TRAFFIC', dept_time, startIP, endIP
    for y in range(0, endIter):
        for j in range(0, 4):
            i = random.randint(startIP, endIP -1)
            host[i].cmd('mausezahn h' + str(i) + '-eth0 -c ' + str(sec) + ' -d 1s -b aa:bb:cc:dd:ee:ff -B 10.0.0.100 -t udp &')
        sec -= 1
        if sec == 0:
            WaitTillEndOfSec(1)
            return
        WaitTillEndOfSec(1)

def WaveTrafficMinus(host, startIP, endIP):
    dateTimeObj = dt.now()
    # get the time object from datetime object
    timeObj = dateTimeObj.time()
    dept_time = timeObj.strftime("%H:%M:%S.%f")

    cnt = 0

    print '++ WAVE TRAFFIC', dept_time, startIP, endIP

    for y in range(10, -1, -1):
        for i in range(startIP, endIP):
            for h in range(0, y):
                host[i].cmd('mausezahn h' + str(i) + '-eth0 -c 1 -d 1s -b aa:bb:cc:dd:ee:ff -B 10.0.0.100 -t udp &')
        for j in range(0, cnt):
            x = random.randint(startIP, endIP - 1)
            host[x].cmd('mausezahn h' + str(x) + '-eth0 -c 1 -d 1s -b aa:bb:cc:dd:ee:ff -B 10.0.0.100 -t udp &')
        cnt += 1
        if y == 0:
            cnt -= 3
            WaitTillEndOfSec(1)
            for j in range(0, cnt):
                x = random.randint(startIP, endIP - 1)
                host[x].cmd('mausezahn h' + str(x) + '-eth0 -c 1 -d 1s -b aa:bb:cc:dd:ee:ff -B 10.0.0.100 -t udp &')
            WaitTillEndOfSec(1)
            return
        WaitTillEndOfSec(1)



def GrowingTrafficThread(host):

    BaseTraffic(host, 80, 85, 5, 25)
    WaitTillEndOfSec(1)
    GrowingTraffic(host, 80, 85, 5, 24)
    #---100pkts
    BaseTraffic(host, 85, 90, 10, 25)
    WaitTillEndOfSec(1)
    GrowingTraffic(host, 85, 90, 5, 24)

def PulseTrafficThread(host):
    print '++ PULSE TRAFFIC'
    BaseTraffic(host, 80, 85, 5, 10)
    WaitTillEndOfSec(10)
    print '++ PULSE TRAFFIC'
    BaseTraffic(host, 83, 84, 7, 10)
    BaseTraffic(host, 84, 85, 8, 10)
    BaseTraffic(host, 85, 90, 12, 10)
    WaitTillEndOfSec(10)
    print '++ PULSE TRAFFIC'
    BaseTraffic(host, 83, 85, 5, 10)
    BaseTraffic(host, 90, 91, 7, 10)
    BaseTraffic(host, 91, 92, 8, 10)
    WaitTillEndOfSec(10)
    print '++ PULSE TRAFFIC'
    BaseTraffic(host, 92, 97, 15, 10)
    WaitTillEndOfSec(10)
    print '++ PULSE TRAFFIC'
    BaseTraffic(host, 97, 99, 8, 10)
    BaseTraffic(host, 99, 100, 9, 10)

def WaveTrafficThread(host):
    print '++ WAVE TRAFFIC'
    BaseTraffic(host, 80, 85, 10, 6)
    WaitTillEndOfSec(1)
    WaveTrafficPlus(host, 80, 85, 5, 5)
    #-------
    BaseTraffic(host, 85, 90, 5, 12)
    WaveTrafficMinus(host, 85, 90)
    #-------
    BaseTraffic(host, 85, 90, 5, 11)
    WaitTillEndOfSec(1)
    WaveTrafficPlus(host, 90, 95, 10, 10)
    #-------
    BaseTraffic(host, 95, 100, 5, 12)
    WaveTrafficMinus(host, 95, 100)
    #-------
    BaseTraffic(host, 80, 85, 5, 9)
    WaitTillEndOfSec(1)
    WaveTrafficPlus(host, 80, 85, 8, 8)


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
    # # # # ------
    # print '#Growing pattern...'
    # thread.start_new_thread(GrowingTrafficThread, (host,))
    #
    # # POISON RANDOM
    # for p in range(0, 50):
    #     for j in range(0, 50):
    #         x = random.randint(1, 79)
    #         BaseTraffic(host, x, x + 1, 1, 1)
    #     WaitTillEndOfSec(1)


    # # NoNAttack traffic for 25 users for each 2 seconds
    # x = 1
    # for count in range(0, 25):
    #     BaseTraffic(host, x, x + 25, 2, 2)
    #     x += 25
    #
    #     if x >= 54:
    #         x = 1
    #     WaitTillEndOfSec(2)
    # # ------

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

    # # --------
    # print '#Pulse pattern...'
    # thread.start_new_thread(PulseTrafficThread, (host,))
    #
    # # POISON RANDOM
    # for p in range(0, 50):
    #     for j in range(0, 50):
    #         x = random.randint(1, 79)
    #         BaseTraffic(host, x, x + 1, 1, 1)
    #     WaitTillEndOfSec(1)


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

    #
    # # NoNAttack traffic for 25 users for each 2 seconds
    # x = 1
    # for count in range(0, 25):
    #     BaseTraffic(host, x, x + 25, 2, 2)
    #     x += 25
    #
    #     if x >= 54:
    #         x = 1
    #     WaitTillEndOfSec(2)
    # ------

    # ------
    print '#Wave pattern...'
    thread.start_new_thread(WaveTrafficThread, (host,))

    # POISON RANDOM
    for p in range(0, 50):
        for j in range(0, 50):
            x = random.randint(1, 79)
            BaseTraffic(host, x, x + 1, 1, 1)
        WaitTillEndOfSec(1)

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


    # # # NoNAttack traffic for 25 users for each 2 seconds
    # x = 1
    # for count in range(0, 25):
    #     BaseTraffic(host, x, x + 25, 2, 2)
    #     x += 25
    #
    #     if x >= 54:
    #         x = 1
    #     WaitTillEndOfSec(2)
    # # ------

    # #  NoNAttack traffic 10 and 5 users for each 5 seconds
    # x = 1
    # for count in range(0, 10):
    #
    #     BaseTraffic(host, x, x + 10, 3, 3)
    #     BaseTraffic(host, x + 10, x + 15, 4, 3)
    #     x += 15
    #
    #     if x >= 64:
    #         x = 1
    #
    #     WaitTillEndOfSec(3)

    print 'Running CLI...'
    CLI(net)

    print 'Stopping network...'
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    CreateTopology()
