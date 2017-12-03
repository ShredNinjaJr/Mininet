#ssh -p 2222 mininet@127.0.0.1
#sudo mn --custom ~/leafspine.py --topo mytopo --link tc


from mininet.topo import Topo

class MyTopo( Topo ):

    numSpine = 1
    numLeaf = 2
    numHostPerLeaf = 2

    bwSpineLeaf = 40
    bwLeafHost = 10

    delaySpineLeaf = '0.004ms'
    delayLeafHost = '0.004ms'


    def __init__( self ):

        Topo.__init__( self )

        spines = []
        for i in range(0, self.numSpine):
            spines.append(self.addSwitch('s'+str(i)))

        leafs = []
        for i in range(0, self.numLeaf):
            leafs.append(self.addSwitch('l'+str(i)))

        hosts = []
        for i in range(0, self.numHostPerLeaf*self.numLeaf):
            hosts.append(self.addHost('h'+str(i)))

        linksSpineLeaf = []
        for i in range (0, self.numSpine):
            for j in range (0, self.numLeaf):
                linksSpineLeaf = self.addLink(spines[i], leafs[j], bw=self.bwSpineLeaf, delay=self.delaySpineLeaf)

        linksLeafHost = []
        for i in range (0, self.numLeaf):
            for j in range (0, self.numHostPerLeaf):
                linksLeafHost = self.addLink(leafs[i], hosts[(i*self.numHostPerLeaf)+j], bw=self.bwLeafHost, delay=self.delayLeafHost)


topos = { 'mytopo': ( lambda: MyTopo() ) }