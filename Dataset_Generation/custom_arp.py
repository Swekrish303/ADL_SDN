import sys
from pox.core import core
from pox.openflow import libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.addresses import EthAddr
from pox.lib.revent import EventHalt
import pox.lib.util as poxutil


from topo import ip_to_mac, dpid_to_name

log = core.getLogger()
	
print("Custon ARP is parsed")

def _dpid_to_mac (dpid):
  return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))

class arp_responder(object):

	def __init__(self):
		print("Arp respond created.")
		core.openflow.addListeners(self)
	
	def _handle_ConnectionUp(self, event):
		"""Handles addtion of new switches to the network.
  
		Creates Flow table modification message object to send to the switch.
		Sets it priority to 0x7000 (Exact matches have higher priority than wildcard matches)
		Matches packets with ARP (Address Resolution Protocol) type using OpenFlow ofp_match object.
		dl_type is ethertype of the packet.
		Fowards the packet to the controller. 
  		OFPP_CONTROLLER is a special virtual port that sends the packet to the controller.
  
		Args:
			event (Event): ConnectionUp event
		"""
		print("ConnectionUp event handler called.")
		fm = of.ofp_flow_mod()
		fm.priority = 0x7000 # Pretty high
		fm.match.dl_type = ethernet.ARP_TYPE
		fm.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
		event.connection.send(fm)

	def _handle_PacketIn(self, event):
		"""Handles packet in messages from the switch.
  		
		event.parse() parses the raw packet data into a packet object.
		find('arp') finds encapsulated packet of given type retuens None if packet is not of given type.
		Creates an ARP packet.
		hw denotes MAC adress, proto denotes IP address.
		Sets the ARP packet's hwtype, prototype, hwlen, protolen as per original ARP packet.
		Sets this as ARP reply packet.
		Sets the ARP packet's hwdst, protodst as per src of the original ARP packet.
		Get the MAC address of the dest using IP address based on Mininet Topology.
		Add Ethernet header to the ARP packet.
		Create an OpenFlow packet out message with Ethernet packet as data.
		OFPP_IN_PORT is a special virtual port that sends the packet back out ots incoming/receivong port.
		msg.in_port is the switch port on which the packet came.
  
    
    	Args:
      		event (Event): PacketIn event
			event has attributes:
   				.port(port of the switch on which packet generating this ofp message came), 
       			.data(raw packet data), .parsed(packet), .ofp, .connection, .dpid
          
        Returns:
		  EventHalt: Stops further handlers from being called for this event.
        """
		dpid = event.connection.dpid
		inport = event.port
		packet = event.parsed
		if not packet.parsed:
			log.warning("%s: ignoring unparsed packet", dpid_to_name(dpid))
			return

		a = packet.find('arp')
		if not a: return

		log.debug("%s ARP %s %s => %s", dpid_to_name(dpid), {arp.REQUEST:"request",arp.REPLY:"reply"}.get(a.opcode,'op:%i' % (a.opcode,)), str(a.protosrc), str(a.protodst))

		packet = event.parsed
		# print(packet)
		arp_req = packet.find('arp')
		if not arp_req: return

		arp_response = arp()
		arp_response.hwtype = arp_req.hwtype
		arp_response.prototype = arp_req.prototype
		arp_response.hwlen = arp_req.hwlen
		arp_response.protolen = arp_req.protolen
		arp_response.opcode = arp.REPLY
		arp_response.hwdst = arp_req.hwsrc
		arp_response.protodst = arp_req.protosrc
		arp_response.protosrc = arp_req.protodst
		mac = EthAddr(ip_to_mac(arp_req.protodst.toStr()))
		arp_response.hwsrc = mac

		e = ethernet(type=packet.type, src=mac, dst=arp_req.hwsrc)
		e.payload = arp_response
		msg = of.ofp_packet_out()
		msg.data = e.pack()
		msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
		msg.in_port = event.port
		event.connection.send(msg)
		event.halt = True
		
		return EventHalt
	
@poxutil.eval_args
def launch ():
	print('Is lauch funct ever called?')
    # Pass classname to core.registerNew
	core.registerNew(arp_responder)
	print("ARP Responder running.")