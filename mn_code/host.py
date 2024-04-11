import sys
import time
from socket import socket, AF_INET, SOCK_STREAM
import re

# Host script for running data from Mininet host to gateway host through socket programming.
# How to run:
# python host.py <data_file>

# Check if file was provided
if len(sys.argv) == 1:
    print("ERROR: Please provide a data file.")
    print("How to run: python host.py <data_file>")
    sys.exit()

mqtt_file = ""
opcua_file = ""
# Find out which broker it is
for arg in sys.argv[1:]:
    mqtt_broker = re.findall("MQTT", arg)
    if mqtt_broker:
        mqtt_file = arg

    opcua_broker = re.findall("OPC-UA", arg)
    if opcua_broker:
        opcua_file = arg

mqtt = None
opcua = None

# Open file(s) (data files are in the 'data' folder in the same directory)
if mqtt_file:
    mqtt = open("data/" + mqtt_file, "r")
    mqtt.readline()

if opcua_file:
    opcua = open("data/" + opcua_file, "r")
    opcua.readline()

# --- This is currently only sending to MQTT, would have to adjust it to OPC-UA as well ---
# Set up socket

if mqtt:
    IP = "10.0.0.1" # MQTT IP Address
    PORT = 54321 # port number to use for socket

    mqtt_socket = socket(AF_INET, SOCK_STREAM)
    mqtt_socket.connect((IP, PORT))

    for line in mqtt:
        split = line.split(",")
        data = split[1].strip()

        mqtt_socket.send(bytes(data, 'utf-8'))
        print(data)
        time.sleep(1)

        response = mqtt_socket.recv(1024)
        print(response)



if opcua:
    IP = "10.0.0.2" # OPC-UA IP Address
    PORT = 54321 # port number to use for socket

    opcua_socket = socket(AF_INET, SOCK_STREAM)
    opcua_socket.connect((IP, PORT))

    for line in opcua:
        split = line.split(",")
        data = split[1].strip()

        # We have manipulated some of the data files from before, if it has -1, we start to send out a DDOS attack from this host
        if data == "-1":
            while True:
                # Send some random data, 30 packets per second
                opcua_socket.send(bytes("5", 'utf-8'))
                time.sleep(0.033)

        # If the data is -2, we will start sending data to the backup gateway
        if data == "-2":
            opcua_socket.close()
            IP = "10.0.0.9" # Backup gateway
            opcua_socket = socket(AF_INET, SOCK_STREAM)
            opcua_socket.connect((IP, PORT))
            continue



        opcua_socket.send(bytes(data, 'utf-8'))
        print(data)
        time.sleep(1)

        response = opcua_socket.recv(1024)
        print(response)




# Close files
if mqtt:
    mqtt.close()
if opcua:
    opcua.close()