import json 


dd = dict() 

with open('NL.json', 'r') as f:
    nlnog = json.load(f)

    for n in nlnog:
        lat, lon = n['coordinates'][0].split(',')
        lat, lon = float(lat), float(lon)

        addr = n['ipv4']

        dd[addr] = n
        dd[addr]['lon'] = lon 
        dd[addr]['lat'] = lat

with open('MLAB.csv', 'r') as f:
    for line in f:
        line = line.strip('\n').strip()

        try:
            lat, lon, _, _, _, addr, _, _, _, company, _, _ = line.split(',')
            if company == 'Google LLC':
                lat, lon = lon, lat

        except ValueError:
            lat, lon, _, _, _, addr, _, _, _, _, _, _, _ = line.split(',')
            line.split(',')
            

        addr, _ = addr.split('/')
        
        dd[addr] = {'lon': lon, 'lat': lat}

with open('ipmap-correct.json', 'w') as f:
    json.dump(dd, f)

