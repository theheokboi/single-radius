import re 
import glob 
import json
import time 
import requests 
import pycountry
import numpy as np 
import haversine as hs
import scipy.constants as constant

from geopy.geocoders import Nominatim
from ripe.atlas.cousteau import AtlasResultsRequest

from mypdb import PeeringDB, Location
from myripe import RIPEAtlasClient



geolocator = Nominatim(user_agent="geoapiExercises",timeout=30)
pdb = PeeringDB()

with open('coords.json') as f:
    coords = json.load(f)

ra_c = RIPEAtlasClient() 

def lat_lon_to_city(latitude, longitude):
    try:
        time.sleep(2)
        location = geolocator.reverse(str(latitude)+","+str(longitude),language='en')
        address = location.raw['address']
        city = address.get('city', '')
        country_code = address.get('country_code', '')

        return city, country_code
    except Exception:
        return '', ''

def translate_country_code_to_country(cc):
    return pycountry.countries.get(alpha_2=cc).name

def get_city_opendata_population(city, country):
    # {
    #   'city': {'type': 'uri', 'value': 'http://www.wikidata.org/entity/Q64'},
    #   'population': {
    #       'datatype': 'http://www.w3.org/2001/XMLSchema#decimal',
    #       'type': 'literal',
    #       'value': '3613495'
    #   },
    #   'country': { 
    #       'type': 'uri', 
    #       'value': 'http://www.wikidata.org/entity/Q183'
    #   },
    #   'cityLabel': {
    #       'xml:lang': 'en', 
    #       'type': 'literal', 
    #       'value': 'Berlin'
    #   },
    #   'countryLabel': {
    #       'xml:lang': 'en', 
    #       'type': 'literal', 
    #       'value': 'Germany'
    #   }
    # }
    try:
        tmp = 'https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000&q=%s&sort=population&facet=country&refine.country=%s'
        cmd = tmp % (city, country)
        res = requests.get(cmd)
        dct = json.loads(res.content)
        out = dct['records'][0]['fields']
        return out['population']
    except Exception as e:
        print(e)
        print("Exception getting population info")
        return 0

def city_ranking(city_info, probe_loc):
    # Rank cities
    cities = []
    delimiters = ', ', ' and ', ' - ', '/'
    pattern = '|'.join(map(re.escape, delimiters))

    for type, lst in city_info.items():
        if type == "city_coords":
            for c in lst:
                city, country  = lat_lon_to_city(c[1],c[0])
                if city and country:
                    cities.append((city.lower(), country.lower()))
        else:
            for loc in lst:
                curr = re.split(pattern, loc[0])
                cities.append((curr[0].lower(), loc[1].lower()))
                

    populations = []
    fac_ixp  = []
    distances = []

    cities = dict.fromkeys(cities)
    cities = list(cities.keys())
    for city, country in cities:
        time.sleep(5)
        population = get_city_opendata_population(city, country)

        city_coords = geolocator.geocode(city) 
        distance = hs.haversine(probe_loc,  (city_coords.latitude, city_coords.longitude))

        fac_ixp_curr = pdb.get_num_of_ixps_and_facs_by_city((city,country))

        populations.append(population)
        distances.append(distance)
        fac_ixp.append(fac_ixp_curr)


    pop_scores = np.argsort(populations) # [0, 1, 2]
    fac_ixp_scores = np.argsort(fac_ixp) # [1, 0, 2]
    distance_scores = np.argsort(-1* np.array(distances)) # [1, 2, 0]
    print(distance_scores)
    metrics = np.array([])# compute a score for each city, then rank cities
    
    for index, city in enumerate(cities):
        pop_score = np.where(pop_scores == index)[0] + 1
        pop_score = pop_score[0]
        fac_ixp_score = np.where(fac_ixp_scores == index)[0] + 1
        fac_ixp_score = fac_ixp_score[0]
        distance_score = np.where(distance_scores == index)[0] + 1
        distance_score = distance_score[0]
        score = pop_score*4 + fac_ixp_score*3 + distance_score*2
        print(score)
        metrics = np.append(metrics,score)

    indices = np.argsort(metrics)
    print(indices)

    return cities[indices[-1]] # last index corresponds to the most likely city
    
def get_loc(addr, results): # results is the measurement reuslt from RIPE Atlas 
    measurements = list() 
    
    with open("static/addr_to_city_list.json") as f:
        city_info = json.load(f)
    
    for msm in results:
        avg_rtt = msm['avg'] 
        if avg_rtt == -1:
            continue
        avg_one_way = avg_rtt/2

        if avg_one_way < 10: 
            measurements.append(msm)
    measurements = sorted(measurements, key=lambda x:x['avg'])
    
    if len(measurements) == 0:
        print(f'Address {addr} is un-pingable... OR all meaurements have one-way latency > 10 ms...')
        return 'NaN', 'NaN', 'NaN', 'NaN', 'NaN'

    lowest_rtt = measurements[0]['avg'] / 2 / 1000
    l_pid = measurements[0]['prb_id']
    p_lon, p_lat = ra_c.PID_TO_RIPE_PROBE[l_pid]['geometry']['coordinates'] 
    print(f'Lowest one way RTT is {lowest_rtt*1000: .2f} ms')
    
    city = city_ranking(city_info[addr], (p_lat, p_lon))
    print("City with best ranking is : {}".format(city))
    
    # key = (round(p_lat, 4), round(p_lon, 4))
    # key = str(key)

    # if key not in coords:
    #     print(f'Getting loc for {key}')
    #     r = requests.get(f'https://ipmap-api.ripe.net/v1/worlds/reverse/{t_lat}/{t_lon}').json()
    #     coords[key] = r 

    # radius = lowest_rtt*(2/3)*(constant.speed_of_light/1000) # m to km 
    # print(radius, 'Km')
    
    # city    = coords[key]['locations'][0]['cityNameAscii']
    # c_code  = coords[key]['locations'][0]['countryCodeAlpha2']
    # country = coords[key]['locations'][0]['countryName']

    # return city, c_code, country, p_lon, p_lat



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

