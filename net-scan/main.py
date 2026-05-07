from scapy.all import *
import os, socket, sys
from datetime import datetime
from concurrent.futures import *
import subprocess as sp
#Console
from rich.console import Console
from rich.table import Table
from rich.prompt import IntPrompt

# ==== Handle Arguments ====
argv = sys.argv[1:]
enable_port_scans = False
enable_device_name = False

if '-p' in sys.argv:
    enable_port_scans = True

if '-d' in sys.argv:
    enable_device_name = True

if '-o' in sys.argv:
    idx = (sys.argv).index("-o")

    output_file = sys.argv[idx+1]
    print("Outfile: ", output_file)

# ==== SETUP ====
console = Console()

#Create table
table = Table(title="Scan Results")
table.add_column("IP Address", style="green")
table.add_column("MAC Address", style="yellow")
table.add_column("Vendor", style="white")
table.add_column("Device name", style="light_sky_blue1")
table.add_column("Open ports", style="white")

#Networking Variables
NETWORK = os.getenv("NETWORK")
INTERFACE = os.getenv("INTERFACE")

console.print(f"[bold green]Interface: [/bold green][white]{str(INTERFACE)}[/white]")
console.print(f"[bold green]Network: [/bold green][white]{str(NETWORK)}[/white]")

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

    if not enable_port_scans:
        return open_ports

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
    row_data = []
    data = [ip, mac]
    ports = open_ports(ip)
    vendor = get_vendor(mac, vendors_dict) #Vendor Name ()

    # === Get pc Name ===
    name = rDNS(ip)
    """
    Skip for testing (Slow)
    if not name:
        console.print("[bold red][*] Checking nbtstat...[/bold red]")
        name = nbtstat(ip) #Only works for windows PC works
    """
    data.append(vendor)
    data.append(name)
    data.append(ports)

    #[MAC, IP, Vendor Name, Device Name (if applicable)]

    #console.print(f"[bold red]DEBUG: {data}[/bold red]")
    table.add_row(str(ip), str(mac), str(vendor), str(name), str(ports))
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


console.print(table)

end_time = datetime.now()

time_elapsed = end_time - start_time

print(f"Done in {time_elapsed}.")


