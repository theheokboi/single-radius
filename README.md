#### System Utilities Setup
sudo apt-get install gzip 


#### Download RIPE RISWhois dumps 
wget https://www.ris.ripe.net/dumps/riswhoisdump.IPv4.gz
gzip -d riswhoisdump.IPv4.gz 

#### Sync PeeringDB local copy 
peeringdb sync 