import os 
import json 
import random 
import requests 

import pytricia 


STATIC_PATH = 'static'

class SingleRadius():
    def __init__(self, pdb_c, ra_c):
        self.pdb_c = pdb_c # PeeringDB Client 
        self.ra_c  = ra_c  # RIPE Atlas Client 

        self.as_neighbour = {}
        self.as_neighbour_fn = f'{STATIC_PATH}/as_neighbours.json'


        self.pyt = pytricia.PyTricia()
        
        self.remote = 'https://stat.ripe.net/data/asn-neighbours/data.json'

        self._setup()

    def _setup(self):
        if os.path.exists(self.as_neighbour_fn):
            with open(self.as_neighbour_fn, 'r') as f:
                self.as_neighbour = json.load(f)

        # Load IP prefix to ASN file 
        with open(f'{STATIC_PATH}/riswhoisdump.IPv4', 'r') as f:
            for line in f:
                if not line.strip() or line.startswith('%'):
                    continue 

                asn, prefix, _ = line.strip().split()
                self.pyt.insert(prefix, asn)
    
    def get_as_neighbours(self, asn):
        # fetch from remote if data does not exist in local cache 
        if asn not in self.as_neighbour: 
            print(f'No cache for ASN {asn}. Fetching from remote...')
            self.as_neighbour[asn] = self.fetch_as_neighbours(asn)
        
        return self.as_neighbour[asn]

    def fetch_as_neighbours(self, asn): 
        response = requests.get(f"{self.remote}?resource={asn}")
        all_neighbours = sorted(response.json()['data']['neighbours'], key=lambda x: x['power'])

        # select only ases that are one hop away 
        return list([x['asn'] for x in filter(lambda x: x['power'] == 1, all_neighbours)])

    def get_addr_asn(self, addr):
        return self.pyt.get(addr)

    def initial_probe_selection(self, addr):
        """Section 3.1 of paper https://www.caida.org/catalog/papers/2020_ripe_ipmap_active_geolocation/ripe_ipmap_active_geolocation.pdf"""

        A = list()
        C = list() 
        
        # Step (1): Add AS(t) to A 
        try:
            a_asn = self.get_addr_asn(addr)
            A.append(a_asn)
        except KeyError:
            print(f'Address {addr} can\'t be mapped to ASN')
            return [], []
        
        # Step (2): Add to C the cities where AS(t) has a probe 
        # TODO: use RIPE Atlas Client to do this 

        # Step (3): Add to A the ASes neighbours (BGP distance of 1) of AS(t)
        neighbours = self.get_as_neighbours(a_asn)
        A += neighbours 

        # Get network object for target asn (asn is stored as int in pdb client)
        network = self.pdb_c.get_network(int(a_asn))
        
        if network is None: return [], []

        # Step (4): Add to C the cities with IXPs where AS(t) is present
        for city in network.ixp_cities:
            if city not in C:
                C.append(city)

        # Step (5): Add to A the ASes present at the IXPs identified in step (4) 
        for ixp_as in network.ixp_ases:
            if ixp_as not in A:
                A.append(ixp_as)
        
        # Step (6): Add to C all the cities corresponding to the facilites where AS(t) is present
        for city in network.fac_cities:
            if city not in C:
                C.append(city)

        # Step (7): Add to A the ASes peering at facilities identified in step (6)  
        for fac_as in network.fac_ases:
            if fac_as not in A:
                A.append(fac_as)      

        # Select probes based on the last paragraph in Section 3.1 
        if A or C:
            probe_ids = self.select_probes(A, C)
        else:
            probe_ids = []

        return probe_ids 

    def select_probes(self, A, C):
        probe_ids = []
        try: 
            # Step 1): Select up to 100 random probes from AS(t)
            probes = self.ra_c.get_probes_in_asn(A[0]) # A[0] is the asn target addr is in 
            probes = random.sample(probes, min([len(probes), 100]))
            probe_ids += probes 

            # Step 2): Select up to 10 random probes from each AS in A 
            for asn in A[1:]:  # skip asn that target addr is in 
                if len(probe_ids) < 500:
                    asn_p = self.ra_c.get_probes_in_asn(asn)
                    rand_10_probes = random.sample(asn_p, min([len(asn_p), 10]))
                    probe_ids += rand_10_probes
                else:
                    break 
        except KeyError:
            pass 

        return [str(p_id) for p_id in probe_ids]

    def measure_addr(self, addr):
        probes = self.initial_probe_selection(addr)
        self.ra_c.create_measurement(addr, probes)


    def terminate(self):
        with open(self.as_neighbour_fn, 'w') as f:
            json.dump(self.as_neighbour, f)
        
        self.ra_c.terminate()



