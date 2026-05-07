import sys, os, platform, subprocess
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

#Create display Table
table = Table(title="Network Interfaces")
table.add_column("ID",style="cyan")
table.add_column("Interface",style="green")
table.add_column("IP Address",style="yellow")
table.add_column("MAC Address", style="red")

for idx, iface_info in interfaces.items():
    table.add_row(str(iface_info.index), iface_info.name, str(iface_info.ip), iface_info.mac)

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
    console.print(f"Network interface set to [green]{interface}[/green]")
    break

#Set the env variable (Only works for this session!)
#os.environ["Interface"] = iface_list[choice-1]

#==== Set Env Variables (Persistant) ====

#For Linux System:
if IS_LINUX:

    #Check for existing env var:
    bashrc_path = Path.home() / ".bashrc"
    var_line = f'export INTERFACE=i\"{interface}\"\n'

    #read file
    content = bashrc_path.read_text().split_lines()
    found = False
    new_content = []

    for line in content:
        #Check if an interface already exists in the file
        if line.startswith("export INTERFACE="):
            new_content.append(var_line)


"""
    #Write to bashrc file
    cmd = f"echo \'export INTERFACE=\"{interface}i\"\' >> ~/.bashrc"
    subprocess.run(cmd, shell=True)
    
    #source terminal to load new env var:
    subprocess.run("source ~/.bashrc", shell=True)

    #DEBUG: Print out env var
    var_content = os.getenv("INTERFACE") 
    console.print(f"INTERFACE: [green]{var_content}[/green]")
""" 
elif IS_WINDOWS:
    pass


sys.exit()

