from scapy.all import *
import os, socket, sys, platform
from datetime import datetime
from concurrent.futures import *
import subprocess as sp
#Console
from rich.console import Console
from rich.table import Table
from rich.prompt import IntPrompt

from pathlib import Path
# ==== platform ====
system_os = platform.system()

# ==== Handle Arguments ====
argv = sys.argv[1:]
enable_port_scans = False
enable_device_name = False

#Enable Port Scanning
if '-p' in sys.argv:
    enable_port_scans = True

#Enable device name check
if '-d' in sys.argv:
    enable_device_name = True

#Save to Output File (csv)
if '-o' in sys.argv:
    idx = (sys.argv).index("-o")

    output_file = sys.argv[idx+1]
    print("Outfile: ", output_file)

# ==== SETUP ====
console = Console()

console.print(f"[bold green]{system_os}[/bold green]")

#Networking Variables
NETWORK = os.getenv("NETWORK")
INTERFACE = os.getenv("INTERFACE")


#Temp
if not NETWORK:
    NETWORK ="192.168.40.0/24"
if not INTERFACE:
    INTERFACE ="lo"

console.print(f"[bold green]Interface: [/bold green][white]{str(INTERFACE)}[/white]")
console.print(f"[bold green]Network: [/bold green][white]{str(NETWORK)}[/white]")

#Set the desired NIC interface
conf.iface = INTERFACE

#common ports
PORTS = [80, 443, 21, 22,  25, 110, 143, 993, 3389, 445, 135, 3306, 1433, 123, 139, 554, 5900, 1433, 1434, 3306]

#==== FUNCTIONS ====
#Get IP and MAC
def get_devices():
    #Returns a list of all device ips

    devices = []

    #Broadcast ARP request to all devices on network:
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=NETWORK)
    resp = srp(pkt, timeout=2, verbose=False)[0]
    
    for sent, recv in resp:
        devices.append((recv.psrc, recv.hwsrc))

    return devices

# Check Open Ports
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

#Get Device name (DNS)
def rDNS(ip):
    #The DNS must be setup on network, 
    # often not useable on home/non-configured networks
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return None

#Get Device Name (nbtStat)
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


def _get_vendor_file_location(relative_path:str) -> str:

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path

#Load Vendor Dictionary
def load_oui():
    #file = "oui.txt"
    file = _get_vendor_file_location("oui.txt")

    #Parses oui into a dict
    oui_dict = {}
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "(hex)" in line:
                parts = line.split()
                oui = parts[0].replace("-", "").upper()
                vendor = " ".join(parts[2:])
                oui_dict[oui] = vendor
    
    return oui_dict

#Get Vendor Name
def get_vendor(mac, vendors_dict):
    if not mac:
        return None
    
    prefix = mac.replace(":", "").replace("-", "")[:6].upper()

    return vendors_dict.get(prefix)

# ==== Main Proc Handler ====
def handle_functions(ip, mac) -> list: #Returns a single row of data?
    #row_data = []
    row = [ip, mac]
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

    #Format 'None' as <Blank>
    if not vendor:
        vendor = ""
    if not name:
        name = ""

    row.append(vendor)
    row.append(name)
    row.append(ports)

    #[MAC, IP, Vendor Name, Device Name (if applicable), Open Ports]
    return row

#Get num value of a row of data
def get_row_value(row:list) -> int:
    #Check Value
    ip = row[0]
    value = int((ip.split('.'))[-1])
    return value

#Sort Rows
def sort_rows(rows:list) -> list:
    sorted_rows = []

    for row in rows:

        #Get Row value
        val = get_row_value(row)
        #print("new_val: ", val)
        placed = False

        #if no rows in sorted, add row:
        if len(sorted_rows) == 0:
            sorted_rows.append(row)
            placed = True
            #print("Placed @ 0")


        #print("sorted_rows[0] val:", get_row_value(sorted_rows[0]))

        if not placed:
            #If value smaller than index 0, prepend:
           # print(f"Checking for prepend: new_val: {val}, srt_rw_val:{get_row_value(sorted_rows[0])}")
            if val < get_row_value(sorted_rows[0]):
                sorted_rows.insert(0, row) #Insert row to beginning
                #print(f"INSERTED: {val} [prepended!]")
                placed = True

        if not placed:
            #print("sorted row enumeration...")
            #Starting at index 0, itter through each entry in sorted_rows:
            for idx, sorted_row in enumerate(sorted_rows):
                #If the value is larger, insert at that location (pushes larger value +1 idx)
                #print(f"\tComparing new_val: {val}, against srt_rw_val:{get_row_value(sorted_row)}, idx: {idx}")
                if get_row_value(sorted_row) > val:
                    sorted_rows.insert(idx, row) 
                    placed = True
                    #print(f"INSERTED: {val} @ idx: {idx}")
                    #console.print(f"[light_sky_blue1]{sorted_rows}[/light_sky_blue1]")
                    break

        #If was not placed, put at end:
        if not placed:
            sorted_rows.append(row)
            #print(f"INSERTED: {val} [end]")

    return sorted_rows

# ==== Output Styles ====
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

def _setup_table() -> Table:
    table = Table(title="Scan Results")
    table.add_column("IP Address", style="green")
    table.add_column("MAC Address", style="yellow")
    table.add_column("Vendor", style="white")
    table.add_column("Device name", style="light_sky_blue1")
    table.add_column("Open ports", style="white")
    return table

# ==== MAIN ====
#Create the exectuor:
devices = get_devices()
vendors_dict = load_oui()
start_time = datetime.now()

console.print("Performing Scan...")

#Contains all the output rows:

rows = []
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
        #print_compact(result)

        #Add each row to rows:
        rows.append(result)
#Print out all rows
#print(rows)

table = _setup_table()

rows = sort_rows(rows)

for row in rows:
    table.add_row(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]))

#Print Scan to User
console.print(table)


end_time = datetime.now()
time_elapsed = end_time - start_time
print(f"Done in {time_elapsed}.")
