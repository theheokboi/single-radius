import json 
import time 
import pprint
import datetime 
from ripe.atlas.cousteau import Ping, AtlasSource, AtlasCreateRequest

STATIC_PATH = 'static'


class RIPEAtlasClient():
    def __init__(self, api_key=None):
        # self.api_key = '3c94fc15-d506-4168-86d0-c139ccf0a58a'
        # self.api_key = '8dc13040-80fc-4959-86a9-6ee0eb15ec74'
        # self.api_key = 'eed1b2cd-e4ab-46b9-a698-ea1f1a1635be'
        # self.api_key = '4d78e284-69a2-4434-8402-912b8266e191'

        self.api_key = api_key if api_key is not None else '3c94fc15-d506-4168-86d0-c139ccf0a58a'
        self.log_fname = f"measurements.{datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.csv"
        self.log_f = None 

        self.ALL_PROBES        = [] # all RIPE probe ids
        self.ASN_TO_RIPE_PROBE = {} # asn      to RIPE probe 
        self.PID_TO_RIPE_PROBE = {} # probe id to RIPE probe 

        self.live_measurements = 0 

        self._setup()
    
    def _setup(self): 
        with open(f'{STATIC_PATH}/RIPE_Probes.json', 'r') as f:
            probes = json.load(f)

        for probe in probes:
            if probe['status']['name'] != 'Connected':
                continue
                
            asn = probe['asn_v4']
            pid = probe['id']

            self.ALL_PROBES.append(pid)
            
            if asn not in self.ASN_TO_RIPE_PROBE: # asn: [probe_1, probe_2, ...]
                self.ASN_TO_RIPE_PROBE[asn] = [probe]
            else:
                self.ASN_TO_RIPE_PROBE[asn] += [probe]
                
            if pid not in self.PID_TO_RIPE_PROBE: # probe id to probe object 
                self.PID_TO_RIPE_PROBE[pid] = probe
        
        self.log_f = open(f'{self.log_fname}', 'w')
    
    def get_probes_in_asn(self, asn):
        probes = []
        if asn in self.ASN_TO_RIPE_PROBE:
            probes = [probe['id'] for probe in self.ASN_TO_RIPE_PROBE[asn]]
        return probes
    
    def get_probes_coords_by_asn(self, asn): # get all probe coordinates in an asn 
        coords = [] 
        
        if asn in self.ASN_TO_RIPE_PROBE:
            coords = [coord['geometry']['coordinates'] for coord in self.ASN_TO_RIPE_PROBE[asn]]
        
        return coords 
    
    def create_measurement(self, t_addr, probes, m_type='ping'):
        if not probes:
            print(f'No probes for {t_addr}...')
            return 

        if self.live_measurements >= 100:
            print('Sleeping for 5 mins...')
            time.sleep(5*60)
            self.live_measurements = 0

        print(f'Creating measurement for {t_addr}...')
        if m_type == 'ping':
            ping = Ping(af=4, target=t_addr, description=f"SingleRadius to {t_addr}")
        else:
            raise NotImplementedError
        try:
            source = AtlasSource(
                type='probes', 
                value=','.join(probes),
                requested=len(probes), 
                tags={"include":["system-ipv4-works"]}
                )
        except TypeError:
            print(f'Type error when creating measurement for address {t_addr}')
            return 
        
        a_request = AtlasCreateRequest(
            start_time=datetime.datetime.utcnow(),
            # stop_time=datetime.datetime.utcnow()+datetime.timedelta(seconds=20),
            key=self.api_key,
            measurements=[ping], 
            sources=[source],
            is_oneoff=True
        )

        is_success, response = a_request.create()
    
        if is_success:
            m_id = response['measurements'][0] # measurement id 
            self.log_f.write(f'{t_addr},{m_id}\n') # target address to measurement id mapping 

            if m_id == 0:
                pprint.pprint(response)
            self.live_measurements += 1

            return m_id  
        else:
            try:
                err = response['error']

                if err['code'] == 102: # You are not permitted to run more than 100 concurrent measurements
                    print('Sleeping for 5 mins...')
                    pprint(err)
                    time.sleep(5*60)
                else:
                    pprint.pprint(err)
        
            except:
                pprint.pprint(response)

    def get_all_probes(self):
        return self.ALL_PROBES

    def terminate(self):
        self.log_f.close()


if __name__ == '__main__':
    ra_c = RIPEAtlasClient() 

    print(ra_c.get_probes_in_asn(206238))
    print(ra_c.get_probes_coords_by_asn(206238)) 


    
