#!/usr/bin/python

from mininet.topo import Topo
from mininet.link import TCLink
import re

# utility functions to assign/get DPIDs, ip addresses, mac addresses etc.

def location_to_dpid(core=None, pod=None, switch=None):
    if core is not None:
        # return '0000000010%02x0000'%core
        return f'0000000010{core:02x}0000'
    else:
        # return '000000002000%02x%02x'%(pod, switch)
        return f'000000002000{pod:02x}{switch:02x}'

def pod_name_to_location(name):
    match = re.match('p(\d+)_s(\d+)', name)
    pod, switch = match.group(1, 2)
    return int(pod), int(switch)

def is_core(dpid):
    return ((dpid & 0xFF000000) >> 24) == 0x10

def dpid_to_name(dpid):
    if is_core(dpid):
        core_num = (dpid & 0xFF0000) >> 16
        # return 'c_s%d'%core_num
        return f'c_s{core_num}'
    else:
        pod = (dpid & 0xFF00) >> 8
        switch = (dpid & 0xFF)
        # return 'p%d_s%d'%(pod, switch)
        return f'p{pod}_s{switch}'

def host_to_ip(name):
    match = re.match('p(\d+)_s(\d+)_h(\d+)', name)
    pod, switch, host = match.group(1, 2, 3)
    # return '10.%s.%s.%s'%(pod, switch, host)
    return f'10.{pod}.{switch}.{host}'

def ip_to_mac(ip):
    match = re.match('10.(\d+).(\d+).(\d+)', ip)
    pod, switch, host = match.group(1, 2, 3)
    return location_to_mac(int(pod), int(switch), int(host))

def location_to_mac(pod, switch, host):
    # return '00:00:00:%02x:%02x:%02x'%(pod, switch, host)
    return f'00:00:00:{pod:02x}:{switch:02x}:{host:02x}'

class FatTreeTopo(Topo):

    # build a fat tree topo of size k
    def __init__(self, k = 4):
        super(FatTreeTopo, self).__init__(self, link = TCLink)

        self.k = k
        
        # pods is 2D array of switches of shape (k, k//2)
        pods = [self.make_pod(i) for i in range(k)]

        for core_num in range(int((k/2)**2)):
            dpid = location_to_dpid(core=core_num)
            # s = self.addSwitch('c_s%d'%core_num, dpid=dpid)
            s = self.addSwitch(f'c_s{core_num}', dpid=dpid)

            stride_num = int(core_num // (k/2))
            for i in range(k):
                self.addLink(s, pods[i][stride_num], bw = 25, max_queue_size = 700)

    
    # makes a single pod with its k switches and (k/2)^2 hosts
    def make_pod(self, pod_num):
        lower_layer_switches = [
            # self.addSwitch('p%d_s%d'%(pod_num, i), dpid=location_to_dpid(pod=pod_num, switch=i))
            self.addSwitch(f'p{pod_num}_s{i}', dpid=location_to_dpid(pod=pod_num, switch=i))
            for i in range(int(self.k / 2))
        ]

        for i, switch in enumerate(lower_layer_switches):
            for j in range(2, int(self.k / 2) + 2):
                # h = self.addHost('p%d_s%d_h%d'%(pod_num, i, j),
                h = self.addHost(f'p{pod_num}_s{i}_h{j}',
                    # ip='10.%d.%d.%d'%(pod_num, i, j),
                    ip=f'10.{pod_num}.{i}.{j}',
                    mac=location_to_mac(pod_num, i, j))
                self.addLink(switch, h, bw = 15, max_queue_size = 500)
        
        upper_layer_switches = [
            # self.addSwitch('p%d_s%d'%(pod_num, i), dpid=location_to_dpid(pod=pod_num, switch=i))
            self.addSwitch(f'p{pod_num}_s{i}', dpid=location_to_dpid(pod=pod_num, switch=i))
            for i in range(int(self.k / 2), self.k)
        ]

        for lower in lower_layer_switches:
            for upper in upper_layer_switches:
                self.addLink(lower, upper, bw = 20, max_queue_size = 700)

        return upper_layer_switches
    
topos = {"fattreetopo" : FatTreeTopo}