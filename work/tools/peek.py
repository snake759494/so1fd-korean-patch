import sys

path = sys.argv[1]
off = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0
ln = int(sys.argv[3], 0) if len(sys.argv) > 3 else 256
with open(path, "rb") as f:
    f.seek(off)
    d = f.read(ln)
for i in range(0, len(d), 16):
    row = d[i:i + 16]
    hexs = " ".join(f"{b:02X}" for b in row)
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
    print(f"{off + i:08X}  {hexs:<47}  {asc}")
