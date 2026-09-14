import re
import sys

path = sys.argv[1]
minlen = int(sys.argv[2]) if len(sys.argv) > 2 else 5
pat = re.compile(rb"[\x20-\x7E]{%d,}" % minlen)
data = open(path, "rb").read()
for m in pat.finditer(data):
    print(f"{m.start():08X}  {m.group().decode('latin1')}")
