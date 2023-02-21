import glob 
import json
import requests
import pprint
import scipy.constants as constant
from myripe import RIPEAtlasClient
from ripe.atlas.cousteau import AtlasResultsRequest

with open('coords.json') as f:
    coords = json.load(f)

ra_c = RIPEAtlasClient() 

def get_loc(addr, results):
    measurements = list() 

    for msm in results:
        avg_rtt = msm['avg'] 
        if avg_rtt == -1:
            continue
        avg_one_way = avg_rtt/2

        if avg_one_way < 10: 
            measurements.append(msm)
    measurements = sorted(measurements, key=lambda x:x['avg'])
    
    if len(measurements) == 0:
        print(f'{addr} is un-pingable...')
        return 'NAN', 'NAN', 'NAN', 'NAN', 'NAN'

    lowest_rtt = measurements[0]['avg'] / 2 / 1000
    l_pid = measurements[0]['prb_id']
    p_lon, p_lat = ra_c.PID_TO_RIPE_PROBE[l_pid]['geometry']['coordinates'] 
    print(f'Lowest one way RTT is {lowest_rtt*1000: .2f} ms')

    key = (round(p_lat, 4), round(p_lon, 4))
    key = str(key)

    if key not in coords:
        print(f'Getting loc for {key}')
        r = requests.get(f'https://ipmap-api.ripe.net/v1/worlds/reverse/{t_lat}/{t_lon}').json()
        coords[key] = r 

    radius = lowest_rtt*(2/3)*(constant.speed_of_light/1000) # m to km 
    print(radius, 'Km')
    
    city   = coords[key]['locations'][0]['cityNameAscii']
    c_code = coords[key]['locations'][0]['countryCodeAlpha2']
    country = coords[key]['locations'][0]['countryName']

    return city, c_code, country, p_lon, p_lat



if __name__ == '__main__':
    ff = open('analysis.csv', 'w')

    for m in glob.glob('measurements.*.csv'):
        with open(m) as f:
            for line in f:
                try:
                    addr, m_id = line.strip().split(',')
                    m_id = int(m_id)
                except ValueError:
                    print(f'VALUEERROR: {line}')

                if m_id: 
                    is_success, results = AtlasResultsRequest(msm_id=m_id).create()
                    city, c_code, country, p_lon, p_lat = get_loc(addr, results)
                    ff.write(f'{addr},{city},{c_code},{country},{p_lon},{p_lat},{m_id}\n')
                else:
                    continue
    ff.close()

