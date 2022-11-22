import json 
import ipinfo

with open('ipmap-correct.json', 'r') as f:
    ipmap = json.load(f)

ips = list(ipmap.keys())

access_token = '6c3feddba35073'
handler = ipinfo.getHandler(access_token)
data = handler.getBatchDetails(ips)

with open('ipinfo.json', 'w') as f:
    json.dump(data, f)