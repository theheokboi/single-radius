import tldextract
from collections import OrderedDict

aws_ec2_regions = OrderedDict({
    'us-east-2': 'Ohio', 
    'us-east-1': 'N. Virginia',
    'compute-1': 'N. Virginia',
    'us-west-1': 'N. California', 
    'us-west-2': 'Oregon',
    'af-south-1': 'Cape Town',
    'ap-east-1': 'Hong Kong',
    'ap-southeast-3': 'Jakarta',
    'ap-south-1': 'Mumbai',
    'ap-northeast-3': 'Osaka',
    'ap-northeast-2': 'Seoul',
    'ap-southeast-1': 'Singapore',
    'ap-southeast-2': 'Sydney',
    'ap-northeast-1': 'Tokyo',
    'ca-central-1': 'Canada (Central)',
    'eu-central-1': 'Frankfurt',
    'eu-west-1': 'Ireland',
    'eu-west-2': 'London',
    'eu-south-1': 'Milan',
    'eu-north-1': 'Stockholm',
    'me-south-1': 'Middle East(Bahrain)',
    'me-central-1': 'UAE',
    'sa-east-1': 'Sao Paulo', 
    '-1'       : 'N. Virginia',
})     

def locate(addr, hss):
    locs = []
    for hs in hss:
        hs = hs.strip('.')
        ext = tldextract.extract(hs)
        domain = ext.domain.strip().strip('.').strip("'")

        if domain == 'amazonaws': # amazon ec2 and s3 
            domain_split = hs.split('.')
            ll = len(domain_split)
            
            
            if ll == 5:
                _, zone, ec_type, _, _ = hs.split('.')
            elif ll == 4:
                _, zone, _, _ = hs.split('.')
            elif ll == 3:
                zone, _, _ = hs.split('.')
                
            try:
                loc = aws_ec2_regions[zone]
            except KeyError:
                if zone.startswith('s3'):
                    for k in aws_ec2_regions.keys():
                        if k in zone:
                            loc = aws_ec2_regions[k]
                            break
                else:
                    print(hs, zone)
                    raise(ValueError)
        
        elif domain == 'cloudfront': # amazon cdn
            _, loc, _, _, _ = hs.split('.')
        
        elif domain == '1e100': # google 
            loc, _, _, = hs.split('.')
            iata, _, _ = loc.split('-')
            iata = iata[:3]
            if len(iata) == 3:
                loc = iata
            else:
                continue 
        
        elif domain == 'force': # salesforce
            loc, loc_2, _, _ = hs.split('.')
        
        elif domain == 'facebook':
            ll = hs.split('.')
            if len(ll) == 3: # cdn
                loc, _, _, = hs.split('.')
            if len(ll) == 4: # ns 
                _, _, _, _ = hs.split('.')
        
        elif domain == 'fbcdn':
            loc, _, _, = hs.split('.')
        
        elif domain == 'tfbnw':
            print(hs)
            pass 
        
        elif domain in  set(['akam', 'akamaitechnologies']):
            continue 
        
        elif domain == 'outbrain':
            loc, _, _ = hs.split('.')
        
        elif domain == 'upcloud':
            # print(hs)
            _, loc, _, _ = hs.split('.')
       
        elif domain == 'justin':
            # print(hs)
            _, loc, _, _ = hs.split('.')
        
        elif domain == 'cdn77':
            ll = hs.split('.')
            if len(ll) == 4:
                _, loc, _, _ = ll
            elif len(ll) == 3:
                loc, _, _ = ll
            
        elif domain == 'adnexus':
            _, _, _, loc, _, _ = hs.split('.')
        
        elif domain == 'yahoo':
            continue
        
        elif domain == 'hinet':
            continue 

        else:
            continue 
        locs.append(loc)
    return locs 