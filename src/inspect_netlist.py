import re

netlist_file = "../Dataset/trojan/AES-T100/src/TjFree/aes_clean_netlist.v"

with open(netlist_file, "r") as f:
    content = f.read()

modules = re.findall(r"module\s+(\w+)", content)

print("Modules Found:")
for m in modules:
    print(m)

print("\nTotal Modules:", len(modules))