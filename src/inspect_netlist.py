import re
import sys
import os

if len(sys.argv) != 2:
    print("Usage: python inspect_netlist.py <netlist_file>")
    sys.exit(1)

netlist_file = sys.argv[1]

if not os.path.isfile(netlist_file):
    print(f"Error: '{netlist_file}' does not exist.")
    sys.exit(1)

with open(netlist_file, "r") as f:
    content = f.read()

modules = re.findall(r"\bmodule\b\s+(\w+)", content)

print("Modules Found:")
for m in modules:
    print(m)

print("\nTotal Modules:", len(modules))