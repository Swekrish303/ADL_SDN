#!/usr/bin/env python

from Trash.topo_fstr import FatTreeTopo

from mininet.node import RemoteController
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, warn, error, debug
from mininet.clean import cleanup

from subprocess import Popen, PIPE
import os
import sys
import atexit
import signal
import glob
from time import sleep

K = 4

CONTROLLERS = {
	'2level': 'controller_2level',
	'dijkstra': 'controller_dj'
}

def run_pox(controller_name):
	controller = CONTROLLERS[controller_name]
	p_pox = Popen(
		[os.environ['HOME'] + '/pox/pox.py', 'fakearp', controller, '--topo=fattree,%d'%K, '--install'],
		# make pox ignore sigint so we can ctrl-c mininet stuff without killing pox
		preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
	)
	atexit.register(p_pox.kill)

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print ('usage: sudo ./run_net.py controller [--iperf]')
		sys.exit()

	controller_name = sys.argv[1]
	if controller_name not in CONTROLLERS:
		print('controller must be one of these:', ', '.join(CONTROLLERS.keys()))
		sys.exit()

	atexit.register(cleanup)
	# just in case program gets interrupted before iperfs get killed
	atexit.register(lambda: os.system('killall iperf 2> /dev/null'))

	run_pox(controller_name)

	# wait for pox to come up
	sleep(1)

	topo = FatTreeTopo(K)
	net = Mininet(topo, controller=RemoteController)
	net.start()

	# wait for switches to connect to controller
	sleep(3)
