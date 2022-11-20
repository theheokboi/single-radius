import os 
import glob
import json 

from single_radius import SingleRadius
from mypdb import PeeringDB
from myripe import RIPEAtlasClient
from custom_rules import locate 


cdn_addr = []
with open('RDNS.json', 'r') as f:
    rdns = json.load(f)
    rdns = rdns['positive']
    rdns = {addr.strip().strip("'"): hss for addr, hss in rdns.items()}

with open('cdn_addr.txt', 'r') as f:
    for addr in f:
        addr = addr.strip()
        cdn_addr.append(addr)

unknown_addr = []

for addr in cdn_addr:
    if addr in rdns:
        locs = locate(addr, rdns[addr])
        if locs:
            print(f'Address {addr} is located in {locs}')
            pass 
        else:
            unknown_addr.append(addr)
    else:
        unknown_addr.append(addr)

try: 
    pdb_c = PeeringDB()
    ra_c  = RIPEAtlasClient() 
    sr = SingleRadius(pdb_c, ra_c)
    
    ips = unknown_addr

    known_ips = list()

    for m in glob.glob('*.csv'):
        with open(m) as f:
            for line in f:
                addr, _ = line.strip().split(',')
                known_ips.append(addr)
    known_ips = set(known_ips)

    for ip in ips:
        if ip not in known_ips:
            probes = sr.measure_addr(ip)
            
except Exception as err:
    raise(err)

finally: 
    sr.terminate() 
    pass 