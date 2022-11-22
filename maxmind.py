import json 
import geoip2.webservice


dd = dict() 

with open('ipmap-correct.json', 'r') as f:
    ipmap = json.load(f)

ips = list(ipmap.keys())

with geoip2.webservice.Client(793196, 'AQs1tXXMf91nCZa0', host='geolite.info') as client:
    for i, ip in enumerate(ips):
        print(i, ip)
        response = client.city(ip)

        dd[ip] = {
            'country_iso': response.country.iso_code,
            'country': response.country.name,
            'city': response.city.name,
            'lat': response.location.latitude,
            'lon': response.location.longitude
        }


with open('maxmind.json', 'w') as f:
    json.dump(dd, f)

