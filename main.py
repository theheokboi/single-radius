import os 
import argparse
import glob
import json 

from single_radius import SingleRadius
from mypdb import PeeringDB
from myripe import RIPEAtlasClient
# from custom_rules import locate 

parser = argparse.ArgumentParser(description='CS440 Reproduction Project')
parser.add_argument("--api-key", type=str, nargs='?', const=None,help="API key for RIPE Atlas")
parser.add_argument("--file-name", type=str, nargs='?', help="JSON file containing target addresses")
args = parser.parse_args()
api_key = args.api_key

pdb_c = PeeringDB()
ra_c  = RIPEAtlasClient(api_key) 
sr = SingleRadius(pdb_c, ra_c)

known_ips = list()

f = open('ips.txt')

for ip in f:
    ip = ip.strip() 
    probes = sr.measure_addr(ip)

f.close() 