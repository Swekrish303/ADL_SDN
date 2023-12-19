import topo

# import logging
# import sys
import sys
#import path
#dir = path.Path(__file__).abspath()
#sys.path.append(dir.parent.parent.parent)

from pox.core import core
from pox.openflow import libopenflow_01 as of
from pox.openflow import nicira as nx
from pox.lib.util import dpidToStr
from pox.lib.addresses import IPAddr
import pox.lib.util as poxutil                # Various util functions


print("Installer.py is parsed")
log = core.getLogger()


# controller that installs two level routing table on each switch that connects
class install_2level(object):
    """Controller that installs two level routing table on each switch that connects

    Args:
        object (object): super class of all python objects
    """
    def __init__(self, topo):
        """Initialize the controller with the given topology and k. Adds itself as a listener to openflow events

        Args:
            topo (Mininet Topology): Mininet topology object code for Fat Tree Topology
        """
        print("Installer created")
        # Adds itself as a listener to openflow events
        core.openflow.addListeners(self)
        self.topo = topo
        self.k = self.topo.k

    # Listener for OpenFlow ConnectionUp Event
    def _handle_ConnectionUp(self, event):
        """Event Handler method for when a connection is established with a switch
        Syntax: _handle_<Event Name>(self, event)
        
        Args:
            event (OpenFlow Event): Openflow event when a connection is established with a switch
            Event has attributes: .dpid, .connection, .ofp(OpenFlow Message object)
        """
        print("ConnectionUp event Handler from installer called.")
        name = topo.dpid_to_name(event.dpid)
        dpid = event.dpid
        # connection object is tied to a specific switch and has .dpid/ .eth_addr attributes
        # connection object is used to send messages to the switch and is the source of all events from switch or datapath
        connection = event.connection
        if topo.is_core(dpid):
            self.install_core(connection, dpid, name)
        else:
            self.install_pod(connection, dpid, name)

    def add_route(self, connection, ip, mask, port, priority=100):
        """This method adds a single flow rule to the switch represented by the connection object. The rule matches packets with the specified IP address and mask, and outputs them to the specified port. The priority argument specifies the priority of the rule.

        Args:
            connection (_type_): _description_
            ip (str): Destination IP address in dotted decimal notation from the Packet
            mask (str): IP Mask in dotted decimal notation from the Packet. (e.g. Standard Class B subnet Mask is 255.255.0.0)
            port (int): Port number to which the packet is to be forwarded
            priority (int, optional): Priority to be given to current OpenFlow Rule. Defaults to 100.
        """
        msg = nx.nx_flow_mod()
        msg.priority = priority
        msg.match.append(nx.NXM_OF_ETH_TYPE(0x800))
        msg.match.append(nx.NXM_OF_IP_DST(ip, mask))
        msg.actions.append(of.ofp_action_output(port=port))
        connection.send(msg)
    
    def install_core(self, connection, dpid, name):
        """Install routes onto all core switches

        Args:
            connection (_type_): _description_
            dpid (int): DPID of the switch
            name (str): Name of the switch
        """
        # install routes to each core switch
        for core in range(self.k):
            self.add_route(connection, f'10.{core}.0.0', '255.255.0.0', core+1)
        print('Installed on core switches')

    def install_pod(self, connection, dpid, name):
        """Install routes onto all pod switches

        Args:
            connection (_type_): _description_
            dpid (int): DPID of the switch
            name (str): Name of the switch
        """
        pod, switch = topo.pod_name_to_location(name)
        # upper layer pod switch
        if switch >= self.k / 2:
            for subnet in range(int(self.k/2)):
                self.add_route(connection, f'10.{pod}.{subnet}.0', '255.255.255.0', subnet+1)
        # lower layer pod switch
        else:
            for host in range(2, int(self.k/2) + 2):
                self.add_route(connection, f'10.{pod}.{switch}.{host}', '255.255.255.255', host-1)
        for host in range(2, int(self.k/2) + 2):
            port =  (host - 2 + switch) % int(self.k / 2) + int(self.k / 2) + 1
            self.add_route(connection, f'0.0.0.{host}', '0.0.0.255', port, 50)
        print('Installed on pod switches')


@poxutil.eval_args
def launch ():
    # Pass class name and arguments of its constructor in core.registerNew
    topos = topo.FatTreeTopo(4)
    core.registerNew(install_2level, topos)
    print('Controller loaded')