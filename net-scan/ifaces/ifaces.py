from scapy.all import *
import subprocess as sp
import json

#Get all interfaces:
ifaces = get_if_list()

#Powershell command to get interface adapters to IDs
cmd = "Get-NetAdapter | ConvertTo-Json"
result = sp.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)

data = json.loads(result.stdout)

for item in data:
    i_name = item["Name"]
    i_desc = item["InterfaceDescription"]
    i_guid = item["InterfaceGuid"]

    for iface in ifaces:
        if i_guid in iface:
            i_face = iface
    
    for _ in range(70):
        print("=", end="")

    print(f"\n{i_name} | {i_desc}\n{i_face}\n")



        
