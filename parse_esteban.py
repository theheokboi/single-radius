import ipaddress 
import subprocess 

f = open('rdns_cloud.csv') 
ff = open('ips.txt', 'w')
for line in f:
    try:
        ip = ipaddress.ip_address(line.strip())

        completedPing = subprocess.run(['ping', '-c', '1', '-w', '1', str(ip)],
                                        stdout=subprocess.PIPE,    
                                        stderr=subprocess.STDOUT)
        if (completedPing.returncode == 0):
            ff.write(f'{ip}\n')
        else:
            print(f'{ip} is not pingable')
    except ValueError:
        continue 

ff.close() 
f.close() 