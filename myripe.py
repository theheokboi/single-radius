import json 
import time 
import datetime 
from ripe.atlas.cousteau import Ping, AtlasSource, AtlasCreateRequest

STATIC_PATH = 'static'


class RIPEAtlasClient():
    def __init__(self):
        # self.api_key = '3c94fc15-d506-4168-86d0-c139ccf0a58a'
        # self.api_key = '8dc13040-80fc-4959-86a9-6ee0eb15ec74'
        # self.api_key = 'eed1b2cd-e4ab-46b9-a698-ea1f1a1635be'
        self.api_key = '4d78e284-69a2-4434-8402-912b8266e191'
        self.log_fname = f"measurements.{datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.csv"
        self.log_f = None 

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
            
            if asn not in self.ASN_TO_RIPE_PROBE:
                self.ASN_TO_RIPE_PROBE[asn] = [probe]
            else:
                self.ASN_TO_RIPE_PROBE[asn] += [probe]
                
            if pid not in self.PID_TO_RIPE_PROBE:
                self.PID_TO_RIPE_PROBE[pid] = probe
        
        self.log_f = open(f'{self.log_fname}', 'w')
    
    def get_probes_in_asn(self, asn):
        probes = []
        if asn in self.ASN_TO_RIPE_PROBE:
            probes = [probe['id'] for probe in self.ASN_TO_RIPE_PROBE[asn]]
        return probes
    
    def create_measurement(self, t_addr, probes, m_type='ping'):
        if not probes:
            self.log_f.write(f'{t_addr},0\n')
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
            print(probes)
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
            self.log_f.write(f'{t_addr},{m_id}\n')
        
            self.live_measurements += 1 
        else:
            try:
                err = response['error']
                pprint.pprint(err)
            
            except:
                import pprint
                pprint.pprint(response)


    def terminate(self):
        self.log_f.close()


    
