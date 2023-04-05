import re 
from peeringdb.client import Client
from peeringdb import resource 
from collections import namedtuple
Location = namedtuple('Location', ['city', 'country'])
from fuzzywuzzy import fuzz


class PDBNetwork():
    def __init__(self, n_gen):
        self.id = n_gen.id 
        self.asn = n_gen.asn 

        self.ixps = self._get_ixps(n_gen)
        self.facs = self._get_facs(n_gen)
        self.ixp_cities = list()
        self.fac_cities = list()
        self.ixp_ases   = list() 
        self.fac_ases   = list() 

        self.fmt_len = 70

    def _get_ixps(self, n_gen):
        return sorted(n_gen.netixlan_set.all(), key=lambda x: str(x.ixlan).upper())

    def _get_facs(self, n_gen):
        return sorted(n_gen.netfac_set.all(), key=lambda x: str(x.fac).upper())

    def print_ixps(self):
        msg = 'List of IXPs target AS is peering in'
        print(f'{msg: <{self.fmt_len}}IXP ID')
        print('-'*70)

        for ixp in self.ixps:
            print(f'{str(ixp): <{self.fmt_len}}{ixp.ixlan_id}')
        print('-'*self.fmt_len)
        msg = 'Total number of public peering exchanges:'
        print(f'{msg: <{self.fmt_len}}{len(self.ixps)}')

    def print_facs(self):
        msg = 'List of Private Peering Facilities target AS is peering in'
        print(f'{msg: <{self.fmt_len}}FAC ID')
        print('-'*self.fmt_len)

        for fac in self.facs:
            print(f'{str(fac): <{self.fmt_len}}{fac.fac_id}')
            # print(ixp, ixp.ixlan_id)
        print('-'*self.fmt_len)
        msg = 'Total number of private peering facilities:'
        print(f'{msg: <{self.fmt_len}}{len(self.facs)}')

class PeeringDB():
    def __init__(self):
        self.client = Client() 
        self.ASN_TO_PID = None 
        self._get_asn_to_id()

        # Misc variables 
        self.delimiters = ', ', ' and '
        self.regex_pattern = '|'.join(map(re.escape, self.delimiters))

        # fuzzy matching threshold 
        self.fz_threshold = 80 

    def _get_asn_to_id(self):
        all_networks = self.client.all(resource.Network)
        self.ASN_TO_PID = { x.asn: x.id for x in all_networks }

    def get_num_of_ixps_and_facs_by_city(self, loc):
        count = 0 

        ix = self.client.all(resource.InternetExchange)
        fc = self.client.all(resource.Facility)
        
        for ixp in ix:
            if ixp.country == loc[1] and (fuzz.ratio(loc[0], ixp.city) > self.fz_threshold):
                count += 1 
        for fac in fc:
            if fac.country == loc[1] and (fuzz.ratio(loc[0], fac.city) > self.fz_threshold):
                count += 1

        return count 
            
    def get_network(self, asn):
        try:
            p_id = self.ASN_TO_PID[asn] # get peeringdb id for target asn 
        except KeyError:
            print(f'Target ASN {asn} does not exist in PeeringDB.')
            return None 

        n = PDBNetwork(self.client.get(resource.Network, p_id))

        for ixp in n.ixps:
            ix   = self.client.get(resource.InternetExchange, ixp.ixlan_id)
            # ix_city = re.split(self.regex_pattern, ix.city)
            # n.ixp_cities += [Location(ix_city, str(ix.country))]
            n.ixp_cities += [Location(ix.city, str(ix.country))]

            ixlan = self.client.get(resource.InternetExchangeLan, ixp.ixlan_id)
            # all ASes peered at this ixp 
            as_at_ixp = list(set([x.asn for x in ixlan.netixlan_set.all()]))
            n.ixp_ases += as_at_ixp
        
        for fac in n.facs:
            fac = self.client.get(resource.Facility, fac.fac_id)
            # fac_city = re.split(self.regex_pattern, fac.city)
            # all ASes peered at this fac 
            as_at_fac = list(set([x.local_asn for x in fac.netfac_set.all()]))
            
            n.fac_cities += [Location(fac.city , str(fac.country))]
            # n.fac_cities += [Location(fac_city , str(fac.country))]
            # n.fac_cities += fac_city 
            n.fac_ases += as_at_fac

        n.ixp_ases = list(set(n.ixp_ases))
        n.fac_ases = list(set(n.fac_ases))

        return n 


if __name__ == '__main__':
    pdb = PeeringDB()
    net = pdb.get_network(9924)

    
    print(net.ixp_cities)
    print(net.fac_cities)
    print(len(net.ixp_ases))
    print(len(net.fac_ases))

    pdb.get_num_of_ixps_and_facs_by_city('test') 
    
