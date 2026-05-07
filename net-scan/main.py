from scapy.all import *
import os
from datetime import datetime
#Threadpool:
from concurrent.futures import *
import socket
import subprocess as sp

# ==== SETUP ====
#Networking Variables
NETWORK = os.getenv("network")
INTERFACE = os.getenv("ETHER_IFACE")
#INTERFACE = os.getenv("WIFI_IFACE")

#Set the desired NIC interface
conf.iface = INTERFACE

#common ports
PORTS = [80, 443, 21, 22,  25, 110, 143, 993, 3389, 445, 135, 3306, 1433, 123, 139, 554, 5900, 1433, 1434, 3306]

#==== FUNCTIONS ====
def get_devices():
    #Returns a list of all device ips

    devices = []

    #Broadcast ARP request to all devices on network:
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=NETWORK)
    resp = srp(pkt, timeout=2, verbose=False)[0]
    
    for sent, recv in resp:
        devices.append((recv.psrc, recv.hwsrc))

    return devices


def open_ports(ip):
    open_ports = []

    for port in PORTS:
        try:
            with socket.create_connection((ip, port), timeout=0.1):
                open_ports.append(port)
        except:
            pass
    
    return open_ports
# === Get Device Name ===
def rDNS(ip):
    #The DNS must be setup on network, 
    # often not useable on home/non-configured networks
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return None

def nbtstat(ip):
    #Command that returns device name
    cmd = ['nbtstat', '-A', ip]
    try:
        out = sp.check_output(cmd, stderr=sp.DEVNULL, text=True)

        for line in out.splitlines():
            # <00> UNIQUE = computer name
            if "<00>" in line and "UNIQUE" in line:
                return line.split()[0]

    except:
        return None

# =========================

def load_oui():
    #Parses oui into a dict
    oui_dict = {}
    with open("oui.txt", "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "(hex)" in line:
                parts = line.split()
                oui = parts[0].replace("-", "").upper()
                vendor = " ".join(parts[2:])
                oui_dict[oui] = vendor
    
    return oui_dict

def get_vendor(mac, vendors_dict):
    if not mac:
        return None
    
    prefix = mac.replace(":", "").replace("-", "")[:6].upper()

    return vendors_dict.get(prefix)

def handle_functions(ip, mac):
    data = [ip, mac]
    ports = open_ports(ip)
    vendor = get_vendor(mac, vendors_dict)
    # === Get pc Name ===
    name = rDNS(ip)

    if not name:
        name = nbtstat(ip) #Only works for windows PC works

    data.append(vendor)
    data.append(name)
    data.append(ports)

    return data

def print_compact(result):
    print(result[3], " | ",result[2], " | ",result[0], " | ",result[1], " | ",result[4])

def print_csv(result):
    print(result[3], ", ",result[2], ", ",result[0], ", ",result[1], ", ",result[4])

def print_detailed(result): 
    print("====================================================================================")
    print("Name: ", result[3])
    print("Vendor: ", result[2])
    print("IP: ", result[0])
    print("MAC: ", result[1])
    print("Open Ports: ", result[4])
    print()
# ==== MAIN ====

#Create the exectuor:

devices = get_devices()
vendors_dict = load_oui()
start_time = datetime.now()

#max_workers is max # of threads, for lan sockets:(50-64)
with ThreadPoolExecutor(max_workers=128) as executer:
    #futures contains the results of everything
    futures = []

    #For each ip, submit a request to use afunction
    for device in devices:
        ip = device[0]
        mac = device[1].upper()

        futures.append(executer.submit(handle_functions, ip, mac))

    for future in as_completed(futures):
        result = future.result()
        print_compact(result)




end_time = datetime.now()

time_elapsed = end_time - start_time

print(f"Done in {time_elapsed}.")


