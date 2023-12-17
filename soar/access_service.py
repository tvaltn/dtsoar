import requests

class Access_Service:
    def __init__(self, ip):
        self.ip = ip

    def enable_access_rules(self):
        policies = open('policies.rego').read()
        response = requests.put(f'http://{self.ip}:8181/v1/policies/access_policies', data=policies)
        #response = requests.get(f'http://{self.ip}:8181/v1/policies')
        print(response.text)
