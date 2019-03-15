#!/usr/bin/python

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import time


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

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    print 'Creating links...'
    net.addLink(h1, s1, bw=100)
    net.addLink(h2, s1, bw=100)
    net.addLink(h3, s1, bw=100)

    net.addLink(h4, s2, bw=100)
    net.addLink(h5, s2, bw=100)

    net.addLink(h6, s3, bw=100)
    net.addLink(h7, s3, bw=100)
    net.addLink(h8, s3, bw=100)

    net.addLink(s1, s2, bw=100)
    net.addLink(s2, s3, bw=100)

    print 'Starting network...'
    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])

    print 'Verifying connectivity...'
    #loss = net.pingAll()

    print '*** Iperf flood...'
    h1, h2 = net.getNodeByName('h1', 'h2')
    #h2.cmd('iperf -c 10.0.0.1 -i 0.5 -t 10 &')
    h1.cmd('iperf -c 10.0.0.10 -t 10 &')


    print 'Running CLI...'
    CLI(net)

    print 'Stopping network...'
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    CreateTopology()
