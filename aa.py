import json 
import pprint

dd = dict() 

with open('Combined.txt') as f:
    for line in f:
        line = line.strip('"\n')
        l = json.loads(line)

        try:
            addr, _ = l['ipv4'].split('/')
        except ValueError:
            addr = l['ipv4']
        except AttributeError:
            continue 


        try:
            lat, lon = l['coordinates'][0].split(',')
        except AttributeError:
            lat, lon = l['coordinates']
        

        dd[addr] = l 
        dd[addr]['lon'] = lon
        dd[addr]['lat'] = lat 


d1 = dict(list(dd.items())[len(dd)//2:])
d2 = dict(list(dd.items())[:len(dd)//2])

with open('ipmap-1.json', 'w') as f:
    json.dump(d1, f)

with open('ipmap-2.json', 'w') as f:
    json.dump(d2, f)


        


