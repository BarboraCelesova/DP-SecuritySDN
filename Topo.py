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
    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')
    h3 = net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3/24')
    h4 = net.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4/24')
    h5 = net.addHost('h5', mac='00:00:00:00:00:05', ip='10.0.0.5/24')
    h6 = net.addHost('h6', mac='00:00:00:00:00:06', ip='10.0.0.6/24')
    h7 = net.addHost('h7', mac='00:00:00:00:00:07', ip='10.0.0.7/24')
    h8 = net.addHost('h8', mac='00:00:00:00:00:08', ip='10.0.0.8/24')
    h9 = net.addHost('h9', mac='00:00:00:00:00:09', ip='10.0.0.9/24')
    h10 = net.addHost('h10', mac='00:00:00:00:00:10', ip='10.0.0.10/24')
    h11 = net.addHost('h11', mac='00:00:00:00:00:11', ip='10.0.0.11/24')
    h12 = net.addHost('h12', mac='00:00:00:00:00:12', ip='10.0.0.12/24')
    h13 = net.addHost('h13', mac='00:00:00:00:00:13', ip='10.0.0.13/24')
    h14 = net.addHost('h14', mac='00:00:00:00:00:14', ip='10.0.0.14/24')
    h15 = net.addHost('h15', mac='00:00:00:00:00:15', ip='10.0.0.15/24')

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    print 'Creating links...'
    net.addLink(h1, s1)
    net.addLink(h2, s1, bw=100)
    net.addLink(h3, s1, bw=100)
    net.addLink(h4, s1, bw=100)
    net.addLink(h5, s1)

    net.addLink(h6, s1, bw=100)
    net.addLink(h7, s1, bw=100)
    net.addLink(h8, s1)
    net.addLink(h9, s2, bw=100)
    net.addLink(h10, s2, bw=100)

    net.addLink(h11, s2)
    net.addLink(h12, s2, bw=100)
    net.addLink(h13, s2, bw=100)
    net.addLink(h14, s2, bw=100)
    net.addLink(h15, s2)

    net.addLink(s1, s2)

    print 'Starting network...'
    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])

    print 'Verifying connectivity...'
    #loss = net.pingAll()

    host = {}

    print '*** Iperf flood...'
    for i in range(1, 16):
        host[i] = net.getNodeByName('h' + str(i))

    #5 -i 0.2 -t 5 // 5 v jednej sekunde
    #host[2].cmd('iperf -c 10.0.0.1 -u -i 0.2 -t 5 &> h2.txt &')
    #27 -t 5 // 3 v jednej sekunde (9 sekund)
    #host[1].cmd('iperf -c 10.0.0.101 -u -t 5 &> h1.txt &')
    print '#Growing pattern'
    #NoNattack traffic
    # for i in [2,3,4,6,7,9,10,12,13,14]:
    #     for j in range(1,6):
    #         host[i].cmd('hping3 -D -c 50 -i 1 -2 10.0.0.10' + str(j) + ' &')


    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

    #Attack traffic
    for i in [1,5,8,11,15]:
        for j in range(1, 6):
            host[i].cmd('iperf -c 10.0.0.10' + str(j) + ' -u -t 10 &')
            # host[i].cmd('hping3 -D -c 50 -i 1 -2 10.0.0.10' + str(j) + ' &> h' + str(i) + '.txt &')

    timer = 49

    t = datetime.datetime.utcnow()
    sleeptime = 1 - (t.microsecond / 1000000.0)
    time.sleep(sleeptime)

    # time.sleep(1)
    for j in range(106,115):
        for i in [1,5,8,11,15]:
            host[i].cmd('iperf -c 10.0.0.' + str(j) + ' -u -t 10 &')
            # host[i].cmd('hping3 -D -c ' + str(timer) + ' -i 1 -2 10.0.0.' + str(j) + ' &> h' + str(i) + '.txt &')
            timer -= 1
            t = datetime.datetime.utcnow()
            sleeptime = 1 - (t.microsecond / 1000000.0)
            time.sleep(sleeptime)

    # for i in [1, 5, 8, 11]:
    #     host[i].cmd('hping3 -c ' + str(timer) + ' -i 1 -2 10.0.0.115 &> h' + str(i) + '.txt &')
    #     timer -= 1
    #     time.sleep(1)

    # ///////////////////////////////////////////////////////////

    # t = datetime.datetime.utcnow()
    # print t
    # print t.second
    # print t.microsecond
    # sleeptime = 1 - (t.microsecond / 1000000.0)
    # print sleeptime
    # time.sleep(sleeptime)
    # host[1].cmd('sudo wireshark &')
    #
    # attackers = [1,5,8,11,15]
    # count = 0
    # for n in range(0, 50):
    #     count = 0
    #     for j in range(0, 5 + (n / 5)):
    #         for i in attackers:
    #             host[i].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #             host[i].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #             count += 1
    #     for k in range(0, n % 5):
    #         host[attackers[randint(0, len(attackers) - 1)]].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #         host[attackers[randint(0, len(attackers) - 1)]].cmd('hping3 -c 1 -2 10.0.0.' + str(randint(101, 115)) + ' &')
    #         count += 1
    #     print t.second, count
    #     t = datetime.datetime.utcnow()
    #     sleeptime = 1 - (t.microsecond / 1000000.0)
    #     time.sleep(sleeptime)


    print 'Running CLI...'
    CLI(net)

    print 'Stopping network...'
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    CreateTopology()
