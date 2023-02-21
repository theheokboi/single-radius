import json 
import requests 
import pandas as pd 
from great_circle import great_circle
import pycountry_convert as pc

with open('coords.json') as f:
    coords = json.load(f)

with open('ipmap-correct.json', 'r') as f:
    ipmap = json.load(f)



dd = {}
try:
    with open('analysis.csv', 'r') as f:
        for line in f:
            line = line.strip('\n').strip()
            addr, city, c_code, c_ascii, t_lon, t_lat, m_id = line.split(',')
            
            if city == 'NAN':
                continue 
            
            t_lon, t_lat = float(t_lon), float(t_lat)
            g_lon, g_lat = float(ipmap[addr]['lon']), float(ipmap[addr]['lat'])

            t_d = great_circle(t_lon, t_lat, g_lon, g_lat)

            key = (round(t_lat, 4), round(t_lon, 4))
            key = str(key)

            if key not in coords:
                print(f'Getting loc for {key}')
                r = requests.get(f'https://ipmap-api.ripe.net/v1/worlds/reverse/{t_lat}/{t_lon}').json()
                coords[key] = r 
                        
            c_code = coords[key]['locations'][0]['countryCodeAlpha2']
            continent = pc.country_alpha2_to_continent_code(c_code)

            if continent not in dd:
                dd[continent] = [t_d]
            else:
                dd[continent].append(t_d)  
    
    
    # df_t = pd.DataFrame(dd)

    dd = {k: sorted(list(map(lambda x: x if x > 1 else 1, v))) for k, v in dd.items()}
    
    for k, v in dd.items():
        print(k, len(v))

    import seaborn as sns
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    fig.set_size_inches(10, 5)
    # fig.tight_layout()

    sns.ecdfplot(
        ax=ax,
        data=dd['AF'], 
        label='AF',
        color='blue',
        log_scale=True,
    )
    sns.ecdfplot(
        ax=ax,
        data=dd['NA'], 
        label='NA',
        color='orange',
        log_scale=True,
    )
    sns.ecdfplot(
        ax=ax,
        data=dd['SA'], 
        label='SA',
        color='green',
        log_scale=True,
    )
    sns.ecdfplot(
        ax=ax,
        data=dd['AS'], 
        label='AS',
        color='pink',
        log_scale=True,
    )
    sns.ecdfplot(
        ax=ax,
        data=dd['EU'], 
        label='EU',
        color='purple',
        log_scale=True,
    )
    sns.ecdfplot(
        ax=ax,
        data=dd['OC'], 
        label='OC',
        color='brown',
        log_scale=True,
    )

    ax.legend()
    ax.set_xlim(0.75, 15000)
    ax.set_yticks([0.00,0.25,0.5,0.75, 1.00])
    ax.set_xticks([1, 10, 40, 100, 1000, 10000])
    ax.set_ylim(0, 1.05)
    ax.set_xlabel('Error Distance from Ground Truth Location (km)', size='x-large')
    ax.set_ylabel('CDF', size='x-large')

    # ax.set_xticks(range(1,32))
    plt.xticks(fontsize='large')
    plt.yticks(fontsize='large')
    plt.axvline(x=40, color='magenta', linestyle="dashed")
    plt.legend(loc='lower right', fontsize='large')
    plt.grid()
    # plt.show()
    fig.savefig('per_continent.jpg', dpi=300, bbox_inches='tight')





        
finally:
    with open('coords.json', 'w') as f:
        json.dump(coords, f)
