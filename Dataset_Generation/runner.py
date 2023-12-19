from mininet.node import RemoteController
from mininet.net import Mininet
from mininet.link import TCLink
from topo import FatTreeTopo
from subprocess import run
from os import environ
from time import sleep
from pox.core import core

log = core.getLogger()


if __name__ == '__main__':
        
    run([environ['HOME'], "pox/pox.py", 'Adversarial_SDN.custom_arp', 'Adversarial_SDN.installer'])
    
    sleep(2)
    
    topo = FatTreeTopo(4)
    net = Mininet(topo, link = TCLink ,controller = RemoteController)
    net.start()
    log.info("Mininet started")
    
    sleep(4)