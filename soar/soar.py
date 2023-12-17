from firewall_service import Firewall_Service
from access_service import Access_Service
from event_handler import Event_Handler
from data_processor import Data_Processor
from orchestrator import Orchestrator
from action_automator import Action_Automator
from digital_twin import Digital_Twin

import json
import time
import requests
import sys
from threading import Thread
from threading import Event

# SOAR Class that runs the SOAR system.
class Soar:
    def __init__(self, ip):
        firewall = Firewall_Service(ip)
        access = Access_Service(ip)
        event_handler = Event_Handler(ip)
        data_processor = Data_Processor()
        playbook = json.load(open('playbook.json'))
        orchestrator = Orchestrator(playbook)
        action_automator = Action_Automator()

        # Initialize and clean up:
        firewall.enable_all_communication()
        access.enable_access_rules()

        url = "http://localhost:7474/db/neo4j/tx/commit"
        data = {"statements":[
                {"statement":"MATCH ()-[r:QUARANTINE]->() DELETE r"}, # Delete old components in quarantine
                {"statement":"MATCH ()-[r:DATA]->(n:Digital_Twin) DELETE r, n"}, # Delete old Digital Twin data
                {"statement":"MATCH (s:SOAR)-[r:RESPONSE]->(resp:RESPONSE) DELETE s, r, resp"}]} # Delete old SOAR responses
        response = requests.post(url, auth=('neo4j', 'soar-neo4j'), json=data)
        print(response)

        # Set up the Digital Twin
        run_event = Event()
        run_event.set()
        digital_twin = Digital_Twin(ip, run_event)
        thread = Thread(target=digital_twin.data_reception) # seperate thread for digital twin
        thread.start()

        # Infinite loop for the SOAR
        while True:
            try:
                response = event_handler.check_events()
                if response == 0: # no response
                    time.sleep(1)
                    continue
                else:
                    processed_data = data_processor.interpret_event_data(response)
                    for data in processed_data:
                        for ip, value in data.items():
                            response = orchestrator.get_playbook_rule(value, ip)
                            action_automator.automate_plan(firewall, ip, response)
            except KeyboardInterrupt:
                # Clear the event and join the thread to exit the program
                run_event.clear()
                thread.join()
                sys.exit()

# Add Mininet IP Address from CLI
if len(sys.argv) == 1:
    print("ERROR: Please provide Mininet IP Address.")
    print("How to run: python soar.py <mininet_ip>")
    sys.exit()

ip = sys.argv[1]
soar = Soar(ip)