import requests
import time
import sys

from data_processor import Data_Processor

# This Digital Twin should not be considered as a true implementation.
# It receives data from the Shark IDS due to ease of implementation,
# as getting it directly from the Mininet gateway would require NAT configuration.

# There is also no true MQTT/OPC-UA implementation done in this project,
# which the Digital Twin would receive information from in a real-world scenario.

class Digital_Twin:

    def __init__(self, ip, run_event):
        self.ip = ip
        self.length = 0 # keeping track of length to know when new events get added
        self.run_event = run_event # Run event for clean exiting of thread

    def data_reception(self):
        while self.run_event.is_set():
            try:
                response = requests.get(f'http://{self.ip}:8000/digital_twin')
                data = response.json()
                
                if len(data) > self.length: # Then we have received new data
                    leng = self.length
                    self.length = len(data)

                    url = "http://localhost:7474/db/neo4j/tx/commit"

                    for info in data[leng:]:
                        for ip, value in info.items():
                            # Update dashboard
                            db_data = {"statements":[
                                {"statement":"MATCH (host:Component{ip:$ip}) CREATE (host)-[:DATA]->(digital_twin:Digital_Twin{data:$data_var})",
                                "parameters":{"ip": ip, "data_var":value}}]}
                            response = requests.post(url, auth=('neo4j', 'soar-neo4j'), json=db_data)
                            
                time.sleep(1)
            except:
                time.sleep(1)
                continue


