from pyverilog.vparser.parser import parse

netlist = ["../Dataset/trojan/AES-T100/src/TjFree/aes_clean_netlist.v"]

ast, directives = parse(netlist)

print("Successfully parsed!")

print(type(ast))