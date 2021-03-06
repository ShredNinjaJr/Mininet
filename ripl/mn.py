"""Custom topologies for Mininet

author: Brandon Heller (brandonh@stanford.edu)

To use this file to run a RipL-specific topology on Mininet.  Example:

  sudo mn --custom ~/ripl/ripl/mn.py --topo ft,4
"""
from ripl.leafspinetopo import LeafSpineTopo
from ripl.dctopo import FatTreeTopo

topos = { 'ft': FatTreeTopo, 'ls': LeafSpineTopo }
