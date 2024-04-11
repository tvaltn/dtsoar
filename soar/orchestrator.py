import json
import requests
from openai import OpenAI
from collections import deque
from threading import Semaphore

class Orchestrator:
    def __init__(self, run_event, action_automator):
        self.id = 1 # Keeping track of IDs for SOAR Responses
        self.ai_id = 1 # Keeping track of IDs for AI Solutions
        self.run_event = run_event # run event for extra thread
        self.semaphore = Semaphore(0) # semaphore for communication between threads
        self.data_queue = deque() # deque for passing data between threads

        self.action_automator = action_automator

        # In order to keep a Human-in-the-Loop we have made some pre-defined decisions about what responses
        # from the AI can be automated. These are listed here. For our simple use case, we just accept
        # every response from the AI that involves IP 10.0.0.3 and 10.0.0.4
        # Real solutions might want to look into the context of the incident or response from the AI
        self.ai_authorization = ["10.0.0.3", "10.0.0.4"]
    
    # Simple creation of a plan based on data retrieved
        # Address: IP Address of the IoT Device
        # Reason: Processed reason by the Data Processor
        # Value: Value of the data
        # Source: Source where the capture of data originated from (ex IDS or Digital Twin)
    def get_playbook_rule(self, address, reason, value, source):
        print("[ORCHESTRATOR] Getting Playbook Rule")

        playbook = json.load(open('playbook.json'))

        for rule in playbook['Playbook Rules']:
            if rule['Type'] == reason:
                
                # Update database with the SOAR respose
                self.create_database_soar_response(address, reason, rule['Response'], value, source)

                print("---- Host: ", address, ", Response: ", rule['Response'])

                return rule # return the response
        
        # If we did not return, it must mean that there was no appropriate rule found in the playbook
        # Add the data to the queue for the secondary thread
        print("[ORCHESTRATOR] No response found in Playbook. Passing to AI thread")
        self.data_queue.append((address, reason, value, source))
        self.semaphore.release()

        return False
    

    # Method for updating database with the created SOAR Response
    def create_database_soar_response(self, address, reason, response, value, source):
        url = "http://localhost:7474/db/neo4j/tx/commit"

        data = {"statements":[
            {"statement":"MATCH (soar:SOAR{name:$name}) CREATE (soar)-[:RESPONSE]->(response:RESPONSE{soar_id:$soar_id, ip:$ip, reason:$reas, response:$resp, value:$value, source:$source})",
            "parameters":{"name":"SOAR", "soar_id":self.id, "ip": address, "reas":reason, "resp":response, "value":value, "source":source}}]}
        response = requests.post(url, auth=('neo4j', 'soar-neo4j'), json=data)

        self.id += 1 # update id by 1


    # Method for updating database with the created AI Solution
    def create_database_ai_solution(self, reason, response, accepted, reasoning, address):
        url = "http://localhost:7474/db/neo4j/tx/commit"

        data = {"statements":[
            {"statement":"MATCH (ai:AI{name:$name}) CREATE (ai)-[:SOLUTION]->(solution:SOLUTION{ai_id:$ai_id, reason:$reas, response:$resp, accepted:$accepted, reasoning:$reasoning, device_ip:$device_ip})",
            "parameters":{"name":"AI", "ai_id":self.ai_id, "reas":reason, "resp":response, "accepted":accepted, "reasoning":reasoning, "device_ip":address}}]}
        response = requests.post(url, auth=('neo4j', 'soar-neo4j'), json=data)

        self.ai_id += 1 # date id by 1


    # Method for updating playbook with a new rule
    def update_playbook(self, source, type, response, ai_model):
        with open('playbook.json', 'r+') as file:
            playbook = json.load(file)

            length = len(playbook['Playbook Rules'])

            # I'm lazy and for our experiment we will always end up with "Isolate Device" as a response
            # Would need to create the Response Plan in another way if doing it properly
            update = {"Rule_ID:":str(length+1),
                      "Source":source,
                      "Type":type,
                      "Response":response,
                      "Response Plan":{
                        "Service":"ryu_firewall",
                        "Action":"disable_communication",
                        "Parameters":{
                            "host_address":"ip"
                        }
                      }
                      }
            
            playbook['Playbook Rules'].append(update)
            file.seek(0)
            json.dump(playbook, file, indent=4)

        # Update dashboard with Playbook rule
        #self.create_database_soar_response(ai_model, "Missing Playbook Rule", "Update Playbook", "PB Fix", "AI Solution")
        
        
    # Method where an extra thread lies to query the OpenAI,
    # when the orchestrator has an incident with no found response in playbook
    def openai_query(self):
        client = OpenAI()
        ai_model = "gpt-4-turbo-preview"

        while self.run_event.is_set():
            sema = self.semaphore.acquire(timeout=1)
            if not sema:
                continue

            # Get data from the queue
            incident = self.data_queue.popleft()

            address = incident[0]
            reason = incident[1]
            value = incident[2]
            source = incident[3]

            # Query the AI with our incident reason, it sends a response back
            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "You are an expert in Computer/Network Security"},
                    {"role": "system", "content": "You get sent a message that might be a security issue. You only respond 'Isolate Device', 'Update Access Control', 'Update Firmware' or 'Do Nothing' depending on the message. Return reasoning split with newline"},
                    {"role": "user", "content": reason}
                ],
                temperature=0
            )

            # Get full response and split it into response and reason, split with \n
            full_response = response.choices[0].message.content
            split_response = full_response.split("\n")
            ai_response = split_response[0]

            # Get the reasoning from AI if this was requested (Modify the second message sent to AI)
            if len(split_response) > 1:
                # In case the AI response includes several newlines, we ignore those to get the reasoning response.
                for item in split_response[1:]:
                    if item != "":
                        ai_reasoning = item
            else:
                ai_reasoning = "None"
                
            print("[AI Solution] Incident Reason: ", reason, ", AI Response: ", ai_response)

            # If we can automate the response, we should find the IP in the authorization list
            if address in self.ai_authorization:
                # Update the playbook with the new rule
                self.update_playbook("AI Solution", reason, ai_response, ai_model)

                # Update database with SOAR response
                self.create_database_soar_response(address, reason, ai_response, value, "AI / LLM")

                # Update database with AI created solution
                self.create_database_ai_solution(reason, ai_response, "True", ai_reasoning, address)

                # Automate the plan
                plan = self.get_playbook_rule(address, reason, value, source)
                self.action_automator.automate_plan(address, plan)

            else:
                # Update database with AI created solution
                self.create_database_ai_solution(reason, ai_response, "False", ai_reasoning, address)

