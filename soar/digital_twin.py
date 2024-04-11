import requests
import time
import sys
from collections import deque

from data_processor import Data_Processor
from threading import Semaphore
from orchestrator import Orchestrator
from action_automator import Action_Automator

# This Digital Twin should not be considered as a true implementation.
# It receives data from the Shark IDS due to ease of implementation,
# as getting it directly from the Mininet gateway would require NAT configuration which got a bit messy.

# There is also no true MQTT/OPC-UA implementation done in this project,
# which the Digital Twin would receive information from in a real-world scenario.

class Digital_Twin:

    def __init__(self, ip, run_event, orchestrator, action_automator):
        self.ip = ip # IP address of the Mininet server
        self.length = 0 # keeping track of length to know when new events get added
        self.run_event = run_event # Run event for clean exiting of threads
        self.semaphore = Semaphore(0) # Semaphore synchronization for the two threads running in this class

        self.data_processor = Data_Processor() # Data processor for data processing
        self.orchestrator = orchestrator # Orchestrator object
        self.action_automator = action_automator # Action Automator object

        # Keep track of IDs for each host
        self.identification = [{"10.0.0.3":1}, {"10.0.0.4":1}, {"10.0.0.5":1}, {"10.0.0.6":1}, {"10.0.0.7":1}, {"10.0.0.8":1}]

        # Keep track of IP and value of data within the Digital Twin
        # We use a deque as this is thread-safe for pops from the left and appends from the right
        self.data_queue = deque()

        # A simple hack for not getting false positives for when the IDS already knows of the issue
        # This variable could be dynamically updated based on the information in policies.rego
        # But for simulating the data this works just fine
        self.ids_tracker = ["No Value"]

        # Tracker for time, we just use a simple id and increment every second
        self.time = 0

        self.threshold = 40 # Threshold for packets per cycle



    # This method retrieves information about the physical twin and saves it to the database
    def data_reception(self):
        while self.run_event.is_set():
            packet_count = 0 # counting the amount of packets we have received

            try:
                response = requests.get(f'http://{self.ip}:8001/digital_twin')
                data = response.json()
                
                if len(data) > self.length: # Then we have received new data
                    leng = self.length
                    self.length = len(data)

                    url = "http://localhost:7474/db/neo4j/tx/commit"

                    for info in data[leng:]:
                        packet_count += 1 
                        for ip, value in info.items():

                            # Get ID and update it
                            dt_id = 0
                            for d in self.identification:
                                for key, id in d.items():
                                    if key == ip:
                                        dt_id = id
                                        d.update({key:id+1})
                                        break

                            # Update dashboard
                            db_data = {"statements":[
                                {"statement":"MATCH (host:Component{ip:$ip}) CREATE (host)-[:DATA]->(digital_twin:Digital_Twin{dt_id:$dt_id, ip:$ip, data:$data_var})",
                                "parameters":{"dt_id":dt_id, "ip": ip, "data_var":value}}]}
                            response = requests.post(url, auth=('neo4j', 'soar-neo4j'), json=db_data)

                            # Add the data to the queue for the secondary thread
                            self.data_queue.append({ip:value})
                            self.semaphore.release()

            except (requests.exceptions.RequestException) as e:
                print("Digital Twin lost connection to server...")
                print("Retrying in 5 seconds...")
                time.sleep(5)
                continue

            #self.analysis_file() # if doing analysis, comment out if not, it writes to a file
            #self.ddos_analysis(packet_count) # if doing analysis, comment out if not, it writes to a file
            
            #print(packet_count)

            # If packet count is over threshold we trigger a mitigative response to a possible DDOS attack
            if packet_count > self.threshold:
                self.ddos_response()

            time.sleep(0.5)


    # This method processes the digital twin data to check for incidents
    def incident_handler(self):
        while self.run_event.is_set():
            # Try and acquire a semaphore ticket, this will happen whenever new data gets added from the other thread
            sema = self.semaphore.acquire(timeout=1)
            if not sema:
                continue

            # Get data from the queue
            value = self.data_queue.popleft()

            # Process the data
            result = self.data_processor.interpret_event_data([value])

            # If there is no problem with the value, we do nothing with the result and continue to the next
            if result[0][1] == "OK Value":
                continue

            # Check if IDS already knows of this issue, in this case this is a false positive
            if result[0][1] in self.ids_tracker:
                continue

            print("[DIGITAL TWIN] Caught Data Violation")

            # Do two things with the result, first fix the missing access control,
            # and then deploy fix on the data violation
            for ip, reason, value in result:
                response = self.orchestrator.get_playbook_rule(ip, reason, value, "Digital Twin")
                if response:
                    self.ids_tracker.append(reason) # Add the reason to our list to avoid future false positives
                    self.action_automator.automate_plan(ip, response)
                    response = self.orchestrator.get_playbook_rule(ip, "Missing Access Control", "AC Fix", "Digital Twin")
                    self.action_automator.automate_plan(reason, response)

    # Create a DDOS mitigation response, we want to do 2 things;
    # First off, isolate devices that have sent too many packages in the last cycle
    # Second, reroute traffic to a backup gateway where non-infected devices can keep sending data to
    def ddos_response(self):
        isolation_list = []

        # Here you could do some proper checks to see what devices to isolate, but we're taking the easy route
        isolation_list.append("10.0.0.3")
        isolation_list.append("10.0.0.4")

        # Isolate the devices that had too high of a packet count
        for ip in isolation_list:
            response = self.orchestrator.get_playbook_rule(ip, "Packet Count Too High", 0, "Digital Twin")
            self.action_automator.automate_plan(ip, response)
        
        # Deploy the backup gateway
        response = self.orchestrator.get_playbook_rule(0, "DDOS Attack", 0, "Digital Twin")
        self.action_automator.automate_plan(0, response)
        
        

    def analysis_file(self):
        file = open("data/devices.csv", "a")
        file.write(str(self.time))
        for x in self.identification:
            for key, id in x.items():
                file.write(","+ str(id-1))
        file.write("\n")
        file.close()
        self.time += 1

    def ddos_analysis(self, packet_count):
        file = open("data/ddos.csv", "a")
        file.write(str(self.time) + "," + str(packet_count))
        file.write("\n")
        file.close()
        self.time += 1