import requests

# Firewall Service class used for creating and modifying Firewall Rules
# Currently only supporting a RYU REST Firewall on the MQTT Gateway
class Firewall_Service:
    def __init__(self, ip):
        self.ip = ip

    # Function to open communication between two hosts. Needs to be set both ways
    def __open_communication(self, url, dst, src):
        # Set a firewall rule to allow all packets through dst to src
        data = '{"nw_src": "' + src + '/32", "nw_dst": "' + dst + '/32"}'
        response = requests.post(url, data)
        print(response.text)

        # Now add a firewall rule to allow all packets from src to dst
        data = '{"nw_src": "' + dst + '/32", "nw_dst": "' + src + '/32"}'
        response = requests.post(url, data)
        print(response.text)

    # Function to remove communication between two hosts
    def __remove_communication(self, url, src):
        # To remove communication we will remove the respective rule that allowed communication
        # We need to find the rule ID first
        response = requests.get(url)

        for items in response.json():
            for rules in items['access_control_list']:
                for rule in rules['rules']:
                    # Check if the mininet host address exists as either src or dst and delete it
                    # (We are deleting the rules both ways, just like when adding communication)
                    if rule['nw_src'] == src or rule['nw_dst'] == src:
                        rule_id = rule['rule_id']
                        data = '{"rule_id": "' + str(rule_id) + '"}'
                        response = requests.delete(url, data=data)
                        print(response.text)

                    
    # Function used at start-up to enable communication between all hosts and their respective gateway
    def enable_all_communication(self):
        print("[FIREWALL SERVICE] Enabling All Communication")
        
        # First, enable communication
        response = requests.put(f'http://{self.ip}:8080/firewall/module/enable/0000000000000001')
        print(response.text)
        response = requests.put(f'http://{self.ip}:8080/firewall/module/enable/0000000000000002')
        print(response.text)

        # Add a rule to allow sending packets to the MQTT host (reception host) from all other hosts
        firewallURL = f'http://{self.ip}:8080/firewall/rules/0000000000000001' # switch 1
        dst = '10.0.0.1' # MQTT

        self.__open_communication(firewallURL, dst, '10.0.0.3') # HBW
        self.__open_communication(firewallURL, dst, '10.0.0.4') # VGR
        self.__open_communication(firewallURL, dst, '10.0.0.5') # SSC
        self.__open_communication(firewallURL, dst, '10.0.0.6') # DPS
        self.__open_communication(firewallURL, dst, '10.0.0.7') # MPO
        self.__open_communication(firewallURL, dst, '10.0.0.8') # SLD


        # Same rule but for the 3 hosts connecting to the OPC-UA host through the OPC-UA switch
        firewallURL = f'http://{self.ip}:8080/firewall/rules/0000000000000002' # switch 2
        dst = '10.0.0.2' # OPC-UA

        self.__open_communication(firewallURL, dst, '10.0.0.3') # HBW
        self.__open_communication(firewallURL, dst, '10.0.0.4') # VGR
        self.__open_communication(firewallURL, dst, '10.0.0.5') # SSC

    # Function called to isolate a Mininet Host away from its gateway(s)
    def disable_communication(self, host_address):
        print(f"[FIREWALL SERVICE] Disabling Communication From Host {host_address}")

        # Update dashboard
        url = "http://localhost:7474/db/neo4j/tx/commit"
        data = {"statements":[
            {"statement":"MATCH (host:Component{ip:$ip}), (quarantine:Quarantine{name:$name}) CREATE (host)-[:QUARANTINE]->(quarantine)",
                "parameters":{"ip": host_address, "name":"Quarantine"}}]}
        requests.post(url, auth=('neo4j', 'soar-neo4j'), json=data)

        mqttURL = f'http://{self.ip}:8080/firewall/rules/0000000000000001' # switch 1
        opcuaURL = f'http://{self.ip}:8080/firewall/rules/0000000000000002' # switch 2

        self.__remove_communication(mqttURL, host_address)
        self.__remove_communication(opcuaURL, host_address)

    # Function called to enable communication to a mininet host again
    def enable_communication(self, mininet_host):
        firewallURL = f'http://{self.ip}:8080/firewall/rules/0000000000000001' # switch 1
        dst = '10.0.0.1' # MQTT
        self.__open_communication(firewallURL, dst, mininet_host)

        if mininet_host == '10.0.0.3' or mininet_host == '10.0.0.4' or mininet_host == '10.0.0.5':
            firewallURL = f'http://{self.ip}:8080/firewall/rules/0000000000000002' # switch 2
            dst = '10.0.0.2' # OPC-UA
            self.__open_communication(firewallURL, dst, mininet_host)

    # Function called to deploy a backup gateway, currently it just reroutes traffic from hosts from the
    # original OPC-UA gateway to a backup one
    def deploy_backup_gateway(self, mininet_host):
        opcuaURL = f'http://{self.ip}:8080/firewall/rules/0000000000000002' # switch 2
        response = requests.get(opcuaURL)

        dst = "10.0.0.9"

        for items in response.json():
            for rules in items['access_control_list']:
                for rule in rules['rules']:
                    if rule['nw_dst'] != "10.0.0.2":
                        self.__open_communication(opcuaURL, rule['nw_dst'], dst)
