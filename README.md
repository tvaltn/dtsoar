# DTSOAR - Digital Twin Security Orchestration, Automation and Response

## Neo4j/NeoDash

Our SOAR solution uses Neo4j/NeoDash as our database/dashboard.

### Neo4j

To run Neo4j, first build the Docker Image:

```
docker run --name dtsoar_neo4j --detach --publish=7474:7474 --publish=7687:7687 --volume=$HOME/neo4j/data:/data neo4j
```

Then run the Docker Container:

```
docker start -a dtsoar_neo4j
```

Go to http://localhost:7474/

Initialize neo4j with the default username and password, and change the password to the new password:

```
Username: neo4j
Password: neo4j
New password: soar-neo4j
```

To initialize the database:

1. Find the data.cypher file from the data folder in this repo.
2. Copy all the contents and paste them into the query box in Neo4j browser on http://localhost:7474/

### NeoDash

After setting up Neo4j you can run NeoDash by going to http://neodash.graphapp.io/

*Make sure you are using the http procotol, and not the secure protocol.*

To initialize the dashboard:

1. Find the dashboard.json file from the data folder in this repo.
2. Inside NeoDash, after you have created a New Dashboard and added the above shown credentials, click on the left panel on the page.
3. Click on the plus sign, and import dashboard.json.



## Configuring Test Bed

The test bed has 4 programs that run on it:

1. Mininet
2. Ryu SDN Controller
3. Shark (pyshark + Flask)
4. Open Policy Agent

### Initial Set-up:

To run and set-up Mininet, please read this guide:

https://mininet.org/download/

To ensure as little conflicts as possible, you should use option 1 from the guide with VirtualBox and the VM image provided, set up with a **Host-only Adapter on Adapter 2**. This should make it so that you are connecting to Mininet on eth1. Remember to allocate computing resources to the VM in the VirtualBox settings.

This test bed has been developed on Windows 11 with WSL and VirtualBox with Mininet VM.

On VirtualBox you can then start the Mininet VM. The username and password is:

```
username: mininet
password: mininet
```

Inside the mininet terminal, create and retrieve the IP address of the VM:

```
sudo dhclient eth1
ifconfig eth1
```

Copy the mn_code folder from local to the Mininet VM (copies to root, replace "mininet_ip" with the IP address from the VM.):

```
scp -r -P 22 mn_code mininet@<mininet_ip>:~/
```

Next up, create 4 local terminals. In all 4 of them, SSH into the Mininet VM:

```
ssh -Y -X mininet@<mininet_ip>
```

And you are all set up. You might have to update some programs.

### 1 Mininet

Mininet dependencies (if you get a X11 Error):

```
sudo xauth add `xauth list $DISPLAY`
```

To run Mininet:

```
cd mn_code
sudo mn --custom topology.py --topo topo --switch ovsk --controller remote -x
```

### 2 Ryu SDN Controller

Ryu dependencies:

```
pip install gunicorn==20.1.0 eventlet==0.30.2
```

```
pip install ryu
```

To run Ryu:

```
ryu-manager ryu.app.rest_firewall
```

### 3 Shark

Shark dependencies:

```
sudo dpkg-reconfigure wireshark-common
-> YES
```

```
sudo chmod +x /usr/bin/dumpcap
```

```
pip install pyshark
```

```
pip install flask
```

```
pip install requests
```

To run Shark:

```
cd mn_code
python shark.py
```

### 4 Open Policy Agent

Use the Docker image for running OPA:

```
docker run -p 8181:8181 openpolicyagent/opa \run --server --log-level debug
```

## SOAR

SOAR is run on the local machine.

Dependencies:

```
pip install requests
```

**In the .env file, add OpenAI API Key, alongside Mininet IP Address**

Inside the soar directory, run:

```
python soar.py
```

# Running Scenarios

From the pop-up terminals after running mininet, you can run data through the factory components to the gateway.
Run MQTT files for data based experiments, run OPC-UA files for DDOS experiments.

## Running data based scenarios

First off, start the Mininet with topology.py. Then run Ryu, OPA and shark.py and soar.py.

Find the **gw1_MQTT** and run:

```
python gateway.py
```

To run data through a host, open one of the host terminals and run (only MQTT files work here):

```
python host.py <data_file>
```

Example on the DPS terminal:

```
python host.py DPS_MQTT.csv
```

Press Ctrl+V to cancel the host program.

If you want to reset, you have to exit and then re-run:

1. Ryu
2. OPA
3. Shark
4. SOAR

## Running DDOS experiment

First off, start the Mininet topology_opcua.py. Then run Ryu, OPA and shark_opti.py.

Find the **gw1_OPC-UA** and run:
```
python gateway.py
```

To run the DDOS experiment, run the 3 OPC-UA data files in their respective terminals:

```
python host.py HBW_OPC-UA.csv
python host.py SSC_OPC-UA.csv
python host.py VGR_OPC-UA.csv
```
