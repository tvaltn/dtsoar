import pyshark
import requests
from flask import Flask
from threading import Thread

# Global variable anomaly_data. Shark updates with information, flask can retrieve information
anomaly_data = list()

# Global variable twin_data. Useful for simulating a digital twin
twin_data = list()

# Method for requesting OPA authorization
def opa_request(src, dst, data):
    packet = {"input":
                {"packet":
                    {"src":src, "dst":dst, "data":data}}}

    response = requests.post('http://localhost:8181/v1/data/access_policies/violation', json=packet)
    response_data = response.json()

    twin_data.append({src:data}) # saving all data for digital twin purposes

    for key in response_data:
        for value in response_data[key]:
            anomaly_data.append({src:value})
            print("[OPA] Caught Violation")
        
# Method for pyshark network interface monitoring
def shark_monitor():
    print("Shark is swimming...")
    capture = pyshark.LiveCapture(interface='s1_mqtt-eth1')
    for packet in capture:
        try:
            source_address = packet.ip.src
            dest_address = packet.ip.dst

            field_names = packet.tcp._all_fields
            field_values = packet.tcp._all_fields.values()

            # Simple hack to get the last element of the packet payload, which is the data
            for field_name in reversed(field_names):
                for field_value in reversed(field_values):
                    if field_name == 'tcp.payload':
                        # Decode the packet and do an OPA request
                        split = field_value.split(":")
                        data = ""
                        for nr in split:
                            temp = int(nr, 16)
                            data += chr(temp)
                        print(f'{source_address} -- {data}')
                        opa_request(source_address, dest_address, data)
                        break
                break
        except:
            continue

# Flask hosts the REST interface
app = Flask(__name__)

# GET events
@app.route('/events', methods = ['GET'])
def event_monitoring():
    return anomaly_data

# GET digital twin data (simulation purposes)
@app.route('/digital_twin', methods = ['GET'])
def collected_data():
    return twin_data

if __name__ == '__main__':
    thread = Thread(target=shark_monitor) # seperate thread for shark and flask
    thread.start()
    app.run(host='0.0.0.0', port=8000)