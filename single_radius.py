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
        self.addr_to_city_list_fn = f'{STATIC_PATH}/addr_to_city_list.json'
        self.addr_to_city_list = {} 


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
        C_str    = list() 
        C_coords = list() 
        
        # Step (1): Add AS(t) to A 
        try:
            a_asn = self.get_addr_asn(addr)
            A.append(a_asn)
        except KeyError:
            print(f'Address {addr} can\'t be mapped to ASN')
            return []
        
        # Step (2): Add to C the cities where AS(t) has a probe 
        city_coords = self.ra_c.get_coords_by_asn(int(a_asn))
        C_coords += city_coords 

        # Step (3): Add to A the ASes neighbours (BGP distance of 1) of AS(t)
        neighbours = self.get_as_neighbours(a_asn)
        A += neighbours

        # Get network object for target asn (asn is stored as int in pdb client)
        network = self.pdb_c.get_network(int(a_asn))
        
        if network is None: 
            print(f'No network object for address {addr}')
            return []

        # Step (4): Add to C the cities with IXPs where AS(t) is present
        for loc in network.ixp_cities:
            for c in loc.city:
                if c not in C_str:
                    C_str.append(loc)
        # for city in network.ixp_cities:
        #     if city not in C:
        #         C.append(city)

        # Step (5): Add to A the ASes present at the IXPs identified in step (4) 
        for ixp_as in network.ixp_ases:
            if ixp_as not in A:
                A.append(ixp_as)
        
        # Step (6): Add to C all the cities corresponding to the facilites where AS(t) is present
        for loc in network.fac_cities:
            for c in loc.city:
                if c not in C_str:
                    C_str.append(loc)

        # for city in network.fac_cities:
        #     if city not in C:
        #         C.append(city)

        # Step (7): Add to A the ASes peering at facilities identified in step (6)  
        for fac_as in network.fac_ases:
            if fac_as not in A:
                A.append(fac_as)      

        # Select probes based on the last paragraph in Section 3.1 
        if A or C_str or C_coords:
            self.addr_to_city_list[addr] = {
                'city_str': C_str, 
                'city_coords': C_coords 
            }
            probe_ids = self.select_probes(addr, A, C_str, C_coords)
        else:
            print(f'A & C both empty for address {addr}')
            probe_ids = []

        return probe_ids 

    def select_probes(self, addr, A, C_str, C_coords):
        probe_ids = []
        try: 
            # Step 1): Select up to 100 random probes from AS(t)
            probes = self.ra_c.get_probes_in_asn(A[0]) # A[0] is the asn target addr is in 
            probes = random.sample(probes, min([len(probes), 100]))
            probe_ids += probes 

            # Step 2): Select up to 5 random probes from each AS in A 
            for asn in A[1:]:  # skip asn that target addr is in 
                if len(probe_ids) < 200:
                    asn_p = self.ra_c.get_probes_in_asn(asn)
                    rand_10_probes = random.sample(asn_p, min([len(asn_p), 5]))
                    probe_ids += rand_10_probes
                else:
                    break 
        except KeyError:
            pass 
        
        if not probe_ids:
            print(f'No RIPE probe in AS for address {addr}')

        return [str(p_id) for p_id in probe_ids]

    def select_random_probes(self):
        probes = self.ra_c.get_all_probes() 
        return [str(addr) for addr in random.sample(probes, 300)]

    def measure_addr(self, addr):
        probes = self.initial_probe_selection(addr)

        if not probes: # probes is empty
            probes = self.select_random_probes() 
        m_id = self.ra_c.create_measurement(addr, probes)

    def terminate(self):
        with open(self.as_neighbour_fn, 'w') as f:
            json.dump(self.as_neighbour, f)
        
        with open(self.addr_to_city_list_fn, 'w') as f:
            json.dump(self.addr_to_city_list, f)
        
        self.ra_c.terminate()


if __name__ == '__main__':
    from mypdb import PeeringDB
    from myripe import RIPEAtlasClient
    pdb_c = PeeringDB()
    ra_c  = RIPEAtlasClient('3c94fc15-d506-4168-86d0-c139ccf0a58a') 
    sr = SingleRadius(pdb_c, ra_c)

    sr.initial_probe_selection('45.138.229.91')


