from mininet.topo import Topo


class Topology(Topo):

    def __init__(self):

        # Initialize topology
        Topo.__init__(self)

        # Add hosts and switches
        h1 = self.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')
        h3 = self.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3/24')
        h4 = self.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4/24')
        h5 = self.addHost('h5', mac='00:00:00:00:00:05', ip='10.0.0.5/24')
        h6 = self.addHost('h6', mac='00:00:00:00:00:06', ip='10.0.0.6/24')
        h7 = self.addHost('h7', mac='00:00:00:00:00:07', ip='10.0.0.7/24')
        h8 = self.addHost('h8', mac='00:00:00:00:00:08', ip='10.0.0.8/24')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        #TODO set parameter bandwidth for links

        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)

        self.addLink(h4, s2)
        self.addLink(h5, s2)

        self.addLink(h6, s3)
        self.addLink(h7, s3)
        self.addLink(h8, s3)

        self.addLink(s1, s2)
        self.addLink(s2, s3)


topos = {'dptopology': (lambda: Topology())}
