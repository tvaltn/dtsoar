import requests

class Action_Automator:

    # Automate the plan based on the orchestrated response
    def automate_plan(self, service, address, response):
        print("[ACTION AUTOMATOR] Automating Response, Updating Dashboard")
        
        url = "http://localhost:7474/db/neo4j/tx/commit"

        if response == "Disable Communication":
            service.disable_communication(address)

            # Update dashboard
            data = {"statements":[
                {"statement":"MATCH (host:Component{ip:$ip}), (quarantine:Quarantine{name:$name}) CREATE (host)-[:QUARANTINE]->(quarantine)",
                 "parameters":{"ip": address, "name":"Quarantine"}}]}
            requests.post(url, auth=('neo4j', 'soar-neo4j'), json=data)