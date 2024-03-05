#### System Utilities Setup
sudo apt-get install gzip 


#### Download RIPE RISWhois dumps 
wget https://www.ris.ripe.net/dumps/riswhoisdump.IPv4.gz
gzip -d riswhoisdump.IPv4.gz 

#### Sync PeeringDB local copy 
peeringdb sync 



#### AS Relationships
If you want to get AS relationships offline, you need to download CAIDA's as-rel data from https://publicdata.caida.org/datasets/as-relationships/serial-1/.
