import os 
import argparse
import glob
import json 

from single_radius import SingleRadius
from mypdb import PeeringDB
from myripe import RIPEAtlasClient
from custom_rules import locate 


# Create the parser
parser = argparse.ArgumentParser(description='CS440 Reproduction Project')
parser.add_argument("--api-key", type=str, nargs='?', const=None,help="API key for RIPE Atlas")
parser.add_argument("--file-name", type=str, nargs='?', help="JSON file containing target addresses")
args = parser.parse_args()

api_key = args.api_key
file_name = args.file_name

print(api_key) 
print(file_name)

cdn_addr = []
with open('RDNS.json', 'r') as f:
    rdns = json.load(f)
    rdns = rdns['positive']
    rdns = {addr.strip().strip("'"): hss for addr, hss in rdns.items()}

with open(file_name, 'r') as f:
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
    ra_c  = RIPEAtlasClient(api_key) 
    sr = SingleRadius(pdb_c, ra_c)
    
    ips = unknown_addr

    known_ips = list()

    for m in glob.glob('*.csv'):
        with open(m) as f:
            for line in f:
                addr, m_id = line.strip().split(',')
                if int(m_id) != 0:
                    known_ips.append(addr)
    known_ips = set(known_ips)

    for ip in ips:
        if ip not in known_ips:
            probes = sr.measure_addr(ip)
            # print(f'Measuring {ip}')
            
except Exception as err:
    raise(err)

finally: 
    sr.terminate() 
    pass 