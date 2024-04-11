import requests
import json
from data_processor import Data_Processor

class Action_Automator:

    def __init__(self, firewall, access):
        self.ryu_firewall = firewall
        self.opa_access_control = access
        self.data_processor = Data_Processor()

    # Automate the plan based on the orchestrated response
    def automate_plan(self, address, playbook_rule):
        print("[ACTION AUTOMATOR] Automating Response, Updating Dashboard")

        print(playbook_rule)

        plan = playbook_rule['Response Plan']

        service = plan['Service']
        action = plan['Action']

        if service == "ryu_firewall":
            service_call = getattr(self.ryu_firewall, action)
            # In our basic implementation we only need address as a parameter, but if you were to need
            # several, maybe different parameters, you would have to map to the correct ones and then
            # send them to the function
            service_call(address)

        if service == "opa_access_control":
            service_call = getattr(self.opa_access_control, action)
            # Just a hack for now, but whenever we want to update access service, the address variable
            # holds the playbook reason, which we can use here
            rule = self.data_processor.interpret_playbook_data(address)
            service_call(rule)
        




    def old_automate_plan(self, address, response):
        print("[ACTION AUTOMATOR] Automating Response, Updating Dashboard")
        
        url = "http://localhost:7474/db/neo4j/tx/commit"

        if response == "Isolate Device":
            self.firewall.disable_communication(address)

            # Update dashboard
            data = {"statements":[
                {"statement":"MATCH (host:Component{ip:$ip}), (quarantine:Quarantine{name:$name}) CREATE (host)-[:QUARANTINE]->(quarantine)",
                 "parameters":{"ip": address, "name":"Quarantine"}}]}
            requests.post(url, auth=('neo4j', 'soar-neo4j'), json=data)

        if response == "Update Access Control":
            # Just a hack for now, but whenever we want to update access service, the address variable
            # holds the playbook reason, which we can use here
            rule = self.data_processor.interpret_playbook_data(address)
            self.access.update_access_rule(rule)

        if response == "Deploy Backup Gateway":
            self.firewall.deploy_backup_gateway()