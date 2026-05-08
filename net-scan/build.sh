#!/bin/bash
# File to build for linux binaries

python -m PyInstaller --onefile --add-data "oui.txt:." --distpath "./dist/linux/" --workpath "./build/linux/" main.py -n netscan
