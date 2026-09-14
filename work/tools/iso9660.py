"""ISO9660 read/extract helper for PSP UMD images.

Provides directory listing (with LBA/size), extraction, and in-place
same-size replacement of file contents.
"""
import os
import struct
import sys

SECTOR = 2048


class Entry:
    __slots__ = ("name", "lba", "size", "is_dir", "path", "rec_offsets")

    def __init__(self, name, lba, size, is_dir, path):
        self.name = name
        self.lba = lba
        self.size = size
        self.is_dir = is_dir
        self.path = path
        self.rec_offsets = []   # absolute file offsets of the directory records

    def __repr__(self):
        return f"<{'D' if self.is_dir else 'F'} {self.path} lba={self.lba} size={self.size}>"


class Iso:
    def __init__(self, path, mode="rb"):
        self.path = path
        self.f = open(path, mode)
        self._read_pvd()

    def close(self):
        self.f.close()

    def _read_pvd(self):
        self.f.seek(16 * SECTOR)
        pvd = self.f.read(SECTOR)
        assert pvd[1:6] == b"CD001", "not an ISO9660 image"
        self.vol_size = struct.unpack_from("<I", pvd, 80)[0]
        root = pvd[156:156 + 34]
        self.root_lba = struct.unpack_from("<I", root, 2)[0]
        self.root_size = struct.unpack_from("<I", root, 10)[0]

    def read_at(self, lba, size):
        self.f.seek(lba * SECTOR)
        return self.f.read(size)

    def _parse_dir(self, lba, size, parent_path):
        data = self.read_at(lba, size)
        out = []
        off = 0
        base = lba * SECTOR
        while off < len(data):
            rec_len = data[off]
            if rec_len == 0:
                # advance to next sector boundary
                nxt = ((off // SECTOR) + 1) * SECTOR
                if nxt >= len(data):
                    break
                off = nxt
                continue
            rec = data[off:off + rec_len]
            e_lba = struct.unpack_from("<I", rec, 2)[0]
            e_size = struct.unpack_from("<I", rec, 10)[0]
            flags = rec[25]
            name_len = rec[32]
            name = rec[33:33 + name_len]
            if name_len == 1 and name in (b"\x00", b"\x01"):
                off += rec_len
                continue
            nm = name.decode("ascii", "replace")
            if ";" in nm:
                nm = nm.split(";")[0]
            is_dir = bool(flags & 0x02)
            p = parent_path + "/" + nm if parent_path else "/" + nm
            ent = Entry(nm, e_lba, e_size, is_dir, p)
            ent.rec_offsets.append(base + off)
            out.append(ent)
            off += rec_len
        return out

    def walk(self):
        """Yield every Entry in the image, depth-first."""
        stack = [(self.root_lba, self.root_size, "")]
        seen = set()
        while stack:
            lba, size, parent = stack.pop(0)
            if (lba, parent) in seen:
                continue
            seen.add((lba, parent))
            for e in self._parse_dir(lba, size, parent):
                yield e
                if e.is_dir:
                    stack.append((e.lba, e.size, e.path))

    def find(self, path):
        path = path.upper()
        for e in self.walk():
            if e.path.upper() == path:
                return e
        return None

    def read_entry(self, e):
        return self.read_at(e.lba, e.size)


def extract_all(iso_path, out_dir):
    iso = Iso(iso_path)
    n = 0
    total = 0
    for e in iso.walk():
        dest = os.path.join(out_dir, e.path.lstrip("/").replace("/", os.sep))
        if e.is_dir:
            os.makedirs(dest, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        iso.f.seek(e.lba * SECTOR)
        remaining = e.size
        with open(dest, "wb") as g:
            while remaining > 0:
                chunk = iso.f.read(min(1 << 20, remaining))
                if not chunk:
                    break
                g.write(chunk)
                remaining -= len(chunk)
        n += 1
        total += e.size
    iso.close()
    return n, total


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "list":
        iso = Iso(sys.argv[2])
        for e in iso.walk():
            print(f"{'D' if e.is_dir else 'F'} {e.lba:>8} {e.size:>12} {e.path}")
        iso.close()
    elif cmd == "extract":
        n, t = extract_all(sys.argv[2], sys.argv[3])
        print(f"extracted {n} files, {t} bytes")
