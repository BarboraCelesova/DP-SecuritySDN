#!/usr/bin/python

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import time
import datetime

from random import randint


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

    print '*** Iperf flood...'
    for i in range(1, 101):
        host[i] = net.getNodeByName('h' + str(i))

    print '#Growing pattern'

    startTime = datetime.datetime.utcnow()
    sleeptime = 1 - (startTime.microsecond / 1000000.0)
    time.sleep(sleeptime)

    #NoNattack traffic
    for i in range(1, 11):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')

    for i in range(11, 16):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')

    # #Attack traffic
    for i in range(80, 85):
        for j in range(1, 6):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')

    #To wait until beginning of another sec
    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    # # print '### IDEM ZABIJAT ', datetime.datetime.time().strftime("%H:%M:%S.%f")
    for i in range(1, 16):
        host[i].cmd('sudo pkill -9 -f iperf &')

    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

    #---after first 10 seconds

    # NoNattack traffic
    for i in range(16, 26):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')
    for i in range(27, 32):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 9 &')
    #Attack
    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    for i in range(16, 32):
        host[i].cmd('sudo pkill -9 -f iperf &')

    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)
    # ---after first 20 seconds

    # NoNattack traffic
    for i in range(32, 42):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')
    for i in range(43, 48):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')

    # Attack
    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    for i in range(32, 48):
        host[i].cmd('sudo pkill -9 -f iperf &')

    # ---after first 30 seconds

    # NoNattack traffic
    for i in range(48, 59):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')
    for i in range(59, 64):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')

    # Attack
    for j in range(6, 8):
        for i in range(80, 85):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    for i in range(48, 64):
        host[i].cmd('sudo pkill -9 -f iperf &')
    for i in range(80, 85):
        host[i].cmd('sudo pkill -9 -f iperf &')

    # ---after first 40 seconds

    # NoNattack traffic
    for i in range(64, 75):
        for j in range(1, 4):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')
    for i in range(75, 80):
        for j in range(1, 5):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 20 &')

    # Attack traffic
    for i in range(86, 96):
        for j in range(10, 24):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 60 &')

    # To wait until beginning of another sec
    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)


    for i in range(86, 96):
        host[i].cmd('iperf -c 10.0.0.125 -u -t 20 &')
        t = datetime.datetime.utcnow()
        sleeptime = 1 - (t.microsecond / 1000000.0)
        time.sleep(sleeptime)

    for i in range(64, 80):
        host[i].cmd('sudo pkill -9 -f iperf &')
    for i in range(86, 96):
        host[i].cmd('sudo pkill -9 -f iperf &')


    print 'Running CLI...'
    CLI(net)

    print 'Stopping network...'
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    CreateTopology()
