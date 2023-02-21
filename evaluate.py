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

        """ 
        if 131 < t_d:
            print(f'{t_d}, {t_lon}, {t_lat}, {g_lon}, {g_lat}')
        """ 


        ipmap_err_dist.append(t_d)
        mmind_err_dist.append(m_d)
        iinfo_err_dist.append(i_d)

ipmap_err_dist = sorted(ipmap_err_dist) 
mmind_err_dist = sorted(mmind_err_dist)
iinfo_err_dist = sorted(iinfo_err_dist)
ipmap_err_dist = list(map(lambda x: x if x > 1 else 1, ipmap_err_dist))
mmind_err_dist = list(map(lambda x: x if x > 1 else 1, mmind_err_dist))
iinfo_err_dist = list(map(lambda x: x if x > 1 else 1, iinfo_err_dist))

import pandas as pd
df_t = pd.DataFrame({'single-radius': ipmap_err_dist, 'MaxMind': mmind_err_dist, 'IPinfo': iinfo_err_dist})
df_m = df_t.melt(var_name='dataset')

import seaborn as sns
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
fig.set_size_inches(10, 5)
# fig.tight_layout()

sns.ecdfplot(
    ax=ax,
    data=df_t, 
    x='single-radius',
    label='single-radius',
    log_scale=True,
    color='blue'
)
sns.ecdfplot(
    ax=ax,
    data=df_t, 
    x='IPinfo',
    label='IPinfo',
    log_scale=True,
    ls=':',
    color='orange'
)
sns.ecdfplot(
    ax=ax,
    data=df_t, 
    x='MaxMind',
    label='MaxMind',
    log_scale=True,
    ls=':',
    color='green'
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
fig.savefig('error.jpg', dpi=300, bbox_inches='tight')





        