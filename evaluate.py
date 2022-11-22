import json 
from great_circle import great_circle


with open('ipmap-correct.json', 'r') as f:
    ipmap = json.load(f)

with open('maxmind.json', 'r') as f:
    maxmind = json.load(f)

with open('ipinfo.json', 'r') as f:
    ipinfo = json.load(f)

ipmap_err_dist = list() 
mmind_err_dist = list()
iinfo_err_dist = list()

with open('analysis.csv', 'r') as f:
    for line in f:
        line = line.strip('\n').strip()
        addr, city, c_code, c_ascii, t_lon, t_lat, m_id = line.split(',')
        
        if city == 'NAN':
            continue 
        
        t_lon, t_lat = float(t_lon), float(t_lat)
        m_lon, m_lat = maxmind[addr]['lon'], maxmind[addr]['lat']
        i_lon, i_lat = float(ipinfo[addr]['longitude']), float(ipinfo[addr]['latitude'])
        g_lon, g_lat = float(ipmap[addr]['lon']), float(ipmap[addr]['lat'])

        t_d = great_circle(t_lon, t_lat, g_lon, g_lat)
        m_d = great_circle(m_lon, m_lat, g_lon, g_lat)
        i_d = great_circle(i_lon, i_lat, g_lon, g_lat)

        if t_d > m_d+i_d:
            print(t_d, m_d, i_d)


        ipmap_err_dist.append(t_d)
        mmind_err_dist.append(m_d)
        iinfo_err_dist.append(i_d)

ipmap_err_dist = sorted(ipmap_err_dist) 
mmind_err_dist = sorted(mmind_err_dist)
iinfo_err_dist = sorted(iinfo_err_dist)

# exit(-1)
import plotly.express as px
import pandas as pd
df_t = pd.DataFrame({'t_err': ipmap_err_dist, 'm_err': mmind_err_dist, 'i_err': iinfo_err_dist})


fig = px.ecdf(df_t, x=['t_err', 'm_err', 'i_err'], log_x=True)
fig.show()




        