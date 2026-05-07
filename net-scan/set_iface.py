import sys, os, platform, subprocess, socket
from pathlib import Path
from scapy.all import *

#Rich
from rich.console import Console
from rich.table import Table
from rich.prompt import IntPrompt

#Create console object
console = Console()

#==== Check System Platform ====
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
if not (IS_WINDOWS or IS_LINUX):
    console.print("[bold red]Platform not supported: [/bold red]", platform.system())
    sys.exit(1)

#==== Interface Configuration ====
interfaces = conf.ifaces #Get dict of interfaces
iface_list = list(interfaces.keys())
iface_ips = []

#Create display Table
table = Table(title="Network Interfaces")
table.add_column("ID",style="cyan")
table.add_column("Interface",style="green")
table.add_column("IP Address",style="yellow")
table.add_column("MAC Address", style="red")

index = 0
for idx, iface_info in interfaces.items():
    index += 1
    table.add_row(str(index), iface_info.name, str(iface_info.ip), iface_info.mac)
    iface_ips.append(iface_info.ip)

#Display Table to user:
console.print(table)

while True:
    #Prompt user for choice
    choice = IntPrompt.ask("Which interface would you like to use? [ID]")

    #Check if the interface id exists
    if choice <= 0 or choice > len(iface_list):
        console.print(f"[red]Invalid Interface[/red]")
        continue

    #On valid interface selection, exit the loop
    interface = iface_list[choice-1]
    network = iface_ips[choice-1]

    #format network from ip:

    #Temp / Testing??:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    print("NEW IP: ", ip)

    network = network.split('.')
    network[3] = '0/24'
    network = '.'.join(network)
    console.print(f"Network interface set to [green]{interface}[/green]")
    break

#==== Set Env Variables (Persistant) ====

#For Linux System:
if IS_LINUX:

    #Check for existing env var:
    bashrc_path = Path.home() / ".bashrc"
    var_line = f'export INTERFACE=\"{interface}\"\n'
    net_line = f'export NETWORK=\"{network}\"\n'

    #read file
    content = bashrc_path.read_text().splitlines()
    found_int = False
    found_net = False
    new_content = []

    for line in content:
        #Check if an interface already exists in the file
        if line.startswith("export INTERFACE="):
            new_content.append(var_line)
            found_int = True
        #Check if a network already exists
        elif line.startswith("export NETWORK="):
            new_content.append(net_line)
            found_net = True
        
        #If not varline, copy over
        else:
            new_content.append(line)

    #append to existing file if they do not exist
    if not found_int:
        new_content.append(var_line)

    if not found_net:
        new_content.append(net_line)

    #Write back to bashrc file
    with open(bashrc_path, 'w') as f:
        f.write('\n'.join(new_content) + '\n')

    """ #DEBUG 
    console.print("[bold yellow]==== bashrc ====[/bold yellow]")
    for line in new_content:
        console.print(f"[cyan]{line}[/cyan]")
    """
    console.print("run  [bold yellow]source ~/.bashrc[/bold yellow] for changes to take affect.")


elif IS_WINDOWS:
    #Set Env Variables
    subprocess.run(["setx", "INTERFACE", interface], shell=True, 
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    subprocess.run(["setx", "NETWORK", network], shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    console.print("Please restart console for change to take effect.")

sys.exit()

