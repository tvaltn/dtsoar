import json
import requests

class Orchestrator:
    def __init__(self, playbook):
        self.playbook = playbook
    
    # Simple creation of a plan based on data retrieved
    def get_playbook_rule(self, data, address):
        print("[ORCHESTRATOR] Getting Playbook Rule")

        for rule in self.playbook['Playbook Rules']:
            if rule['Type'] == data:
                url = "http://localhost:7474/db/neo4j/tx/commit"
                # Update dashboard
                data = {"statements":[
                    {"statement":"CREATE (soar:SOAR)-[:RESPONSE]->(response:RESPONSE{ip:$ip, reason:$reas, response:$resp})",
                    "parameters":{"ip": address, "reas":rule['Type'], "resp":rule['Response']}}]}
                response = requests.post(url, auth=('neo4j', 'soar-neo4j'), json=data)
                return rule['Response'] # return the response

