#!/usr/bin/env python
'''@package dctopo

Data center network topology creation and drawing.

@author Brandon Heller (brandonh@stanford.edu)

This package includes code to create and draw networks with a regular,
repeated structure.  The main class is StructuredTopo, which augments the
standard Mininet Topo object with layer metadata plus convenience functions to
enumerate up, down, and layer edges.
'''

from mininet.topo import Topo


PORT_BASE = 1  # starting index for OpenFlow switch ports


class NodeID(object):
    '''Topo node identifier.'''

    def __init__(self, dpid = None):
        '''Init.

        @param dpid dpid
        '''
        # DPID-compatible hashable identifier: opaque 64-bit unsigned int
        self.dpid = dpid

    def __str__(self):
        '''String conversion.

        @return str dpid as string
        '''
        return str(self.dpid)

    def name_str(self):
        '''Name conversion.

        @return name name as string
        '''
        return str(self.dpid)

    def ip_str(self):
        '''Name conversion.

        @return ip ip as string
        '''
        hi = (self.dpid & 0xff00) >> 8
        lo = self.dpid & 0xff
        return "10.0.%i.%i" % (hi, lo)


class StructuredNodeSpec(object):
    '''Layer-specific vertex metadata for a StructuredTopo graph.'''

    def __init__(self, up_total, down_total, up_speed, down_speed,
                 type_str = None):
        '''Init.

        @param up_total number of up links
        @param down_total number of down links
        @param up_speed speed in Gbps of up links
        @param down_speed speed in Gbps of down links
        @param type_str string; model of switch or server
        '''
        self.up_total = up_total
        self.down_total = down_total
        self.up_speed = up_speed
        self.down_speed = down_speed
        self.type_str = type_str


class StructuredEdgeSpec(object):
    '''Static edge metadata for a StructuredTopo graph.'''

    def __init__(self, speed = 1.0):
        '''Init.

        @param speed bandwidth in Gbps
        '''
        self.speed = speed


class StructuredTopo(Topo):
    '''Data center network representation for structured multi-trees.'''

    def __init__(self, node_specs, edge_specs):
        '''Create StructuredTopo object.

        @param node_specs list of StructuredNodeSpec objects, one per layer
        @param edge_specs list of StructuredEdgeSpec objects for down-links,
            one per layer
        '''
        super(StructuredTopo, self).__init__()
        self.node_specs = node_specs
        self.edge_specs = edge_specs

    def def_nopts(self, layer):
        '''Return default dict for a structured topo.

        @param layer layer of node
        @return d dict with layer key/val pair, plus anything else (later)
        '''
        return {'layer': layer}

    def layer(self, name):
        '''Return layer of a node

        @param name name of switch
        @return layer layer of switch
        '''
        return self.node_info[name]['layer']

    def isPortUp(self, port):
        ''' Returns whether port is facing up or down

        @param port port number
        @return portUp boolean is port facing up?
        '''
        return port % 2 == PORT_BASE

    def layer_nodes(self, layer):
        '''Return nodes at a provided layer.

        @param layer layer
        @return names list of names
        '''
        def is_layer(n):
            '''Returns true if node is at layer.'''
            return self.layer(n) == layer

        nodes = [n for n in self.g.nodes() if is_layer(n)]
        return nodes

    def up_nodes(self, name):
        '''Return edges one layer higher (closer to core).

        @param name name

        @return names list of names
        '''
        layer = self.layer(name) - 1
        nodes = [n for n in self.g[name] if self.layer(n) == layer]
        return nodes

    def down_nodes(self, name):
        '''Return edges one layer higher (closer to hosts).

        @param name name
        @return names list of names
        '''
        layer = self.layer(name) + 1
        nodes = [n for n in self.g[name] if self.layer(n) == layer]
        return nodes

    def up_edges(self, name):
        '''Return edges one layer higher (closer to core).

        @param name name
        @return up_edges list of name pairs
        '''
        edges = [(name, n) for n in self.up_nodes(name)]
        return edges

    def down_edges(self, name):
        '''Return edges one layer lower (closer to hosts).

        @param name name
        @return down_edges list of name pairs
        '''
        edges = [(name, n) for n in self.down_nodes(name)]
        return edges



class LeafSpineTopo(StructuredTopo):
    '''Three-layer homogeneous Fat Tree.

    From "A scalable, commodity data center network architecture, M. Fares et
    al. SIGCOMM 2008."
    '''
    LAYER_SPINE = 0
    LAYER_LEAF = 1
    LAYER_HOST = 2

    class LeafSpineNodeID(NodeID):
        '''Fat Tree-specific node.'''

  
        def __init__(self, sw = 0, host = 0, dpid = None, name = None):
            '''Create FatTreeNodeID object from custom params.

            Either (pod, sw, host) or dpid must be passed in.

            @param pod pod ID
            @param sw switch ID
            @param host host ID
            @param dpid optional dpid
            @param name optional name
            '''
            if dpid:
                self.sw = (dpid & 0xff00) >> 8
                self.host = (dpid & 0xff)
                self.dpid = dpid
            elif name:
                sw, host = [int(s) for s in name.split('_')]
                self.sw = sw
                self.host = host
                self.dpid = (sw << 8) + host
            else:
                self.sw = sw
                self.host = host
                self.dpid = (sw << 8) + host

        def __str__(self):
            return "(%i, %i)" % (self.sw, self.host)

        def name_str(self):
            '''Return name string'''
            return "%i_%i" % (self.sw, self.host)

        def mac_str(self):
            '''Return MAC string'''
            return "00:00:00:00:%02x:%02x" % (self.sw, self.host)

        def ip_str(self):
            '''Return IP string'''
            return "10.0.%i.%i" % (self.sw, self.host)

    def def_nopts(self, layer, name = None):
        '''Return default dict for a FatTree topo.

        @param layer layer of node
        @param name name of node
        @return d dict with layer key/val pair, plus anything else (later)
        '''
        d = {'layer': layer}
        if name:
            id = self.id_gen(name = name)
            # For hosts only, set the IP
            if layer == self.LAYER_HOST:
              d.update({'ip': id.ip_str()})
              d.update({'mac': id.mac_str()})
            d.update({'dpid': "%016x" % id.dpid})
        return d


    def __init__(self, k = 4, speed = 1.0):
        '''Init.

        @param k switch degree
        @param speed bandwidth in Gbps
        '''
        spine = StructuredNodeSpec(0, k * 2, None, speed, type_str = 'spine')
        leaf = StructuredNodeSpec(k, k / 2, speed, speed, type_str = 'leaf')        
        host = StructuredNodeSpec(1, 0, speed, None, type_str = 'host')
        
        node_specs = [leaf, spine, host]
        edge_specs = [StructuredEdgeSpec(speed)] * 2
        super(LeafSpineTopo, self).__init__(node_specs, edge_specs)

        self.k = k
        self.id_gen = LeafSpineTopo.LeafSpineNodeID
        
        pods = range(0, k)
        core_sws = range(1, k / 2 + 1)
        agg_sws = range(k / 2, k)
        edge_sws = range(0, k / 2)
        hosts = range(2, k / 2 + 2)
        
        spine_sws = range(1, k + 1)
        leaf_sws = range(1, k*2 + 1)
        
        spines = []
        for s in range(0, k):
            spine_id = self.id_gen(0, s).name_str()
            spine_opts = self.def_nopts(self.LAYER_SPINE, spine_id)
            self.addSwitch(spine_id, **spine_opts)
            spines.append(spine_id)
         
        for l in range(0, k * 2):
            leaf_id = self.id_gen(1, l).name_str()
            leaf_opts = self.def_nopts(self.LAYER_LEAF, leaf_id)
            self.addSwitch(leaf_id, **leaf_opts)
            for h in range(0, k / 2):
                host_id = self.id_gen(2, l * (k / 2) + h).name_str()
                host_opts = self.def_nopts(self.LAYER_HOST, host_id)
                self.addHost(host_id, **host_opts)
                self.addLink(host_id, leaf_id)
            for s in spines:
                self.addLink(leaf_id, s)
            
