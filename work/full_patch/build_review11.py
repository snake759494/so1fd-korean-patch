"""Restore ELF metadata for PSP CFW; preserve Review 10's loaded memory image.

Requires the user's original ISO and verified Review 10 ISO locally.
The output is a hardware-test candidate, not proof of PSP compatibility.
"""
from pathlib import Path
import sys, struct, hashlib, json, shutil, subprocess
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
sys.path.insert(0,str(ROOT/'work/tools'))
from iso9660 import Iso

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def rebuild(original,patched):
    orig_ph=struct.unpack_from('<8I',original,52)
    old_phoff=struct.unpack_from('<I',patched,28)[0]
    main_ph=struct.unpack_from('<8I',patched,old_phoff)
    hook_ph=struct.unpack_from('<8I',patched,old_phoff+32)
    assert orig_ph==main_ph and orig_ph[1]==84
    shift=44
    # Keep every original section, its names, and its original runtime address.
    b=bytearray(original[:84]+bytes(shift)+original[84:])
    b[128:128+main_ph[4]]=patched[main_ph[1]:main_ph[1]+main_ph[4]]
    new_shoff=struct.unpack_from('<I',original,32)[0]+shift
    struct.pack_into('<II',b,28,52,new_shoff)
    struct.pack_into('<H',b,44,2)
    first=list(main_ph);first[1]+=shift;first[3]+=shift
    struct.pack_into('<8I',b,52,*first)
    shnum=struct.unpack_from('<H',b,48)[0]
    for i in range(shnum):
        at=new_shoff+40*i
        off=struct.unpack_from('<I',b,at+16)[0]
        if off: struct.pack_into('<I',b,at+16,off+shift)
    b.extend(bytes((-len(b))%16))
    new_hook_offset=len(b)
    payload=patched[hook_ph[1]:hook_ph[1]+hook_ph[4]]
    b.extend(payload)
    second=list(hook_ph);second[1]=new_hook_offset
    struct.pack_into('<8I',b,84,*second)
    assert b[128:128+first[4]]==patched[main_ph[1]:main_ph[1]+main_ph[4]]
    assert b[new_hook_offset:]==payload
    # Match the CFW string-table/module-info lookup, including exact module bytes.
    stridx=struct.unpack_from('<H',b,50)[0]
    s=struct.unpack_from('<10I',b,new_shoff+40*stridx)
    assert s[1]==3
    names=b[s[4]:s[4]+s[5]];found=[]
    for i in range(shnum):
        sec=struct.unpack_from('<10I',b,new_shoff+40*i)
        name=names[sec[0]:].split(b'\0',1)[0]
        if name==b'.rodata.sceModuleInfo':
            found.append(sec[4]);assert b[sec[4]:sec[4]+sec[5]]==original[sec[4]-shift:sec[4]-shift+sec[5]]
    assert found==[first[3]],found
    return bytes(b),dict(loaded_segments_byte_identical=True,program_header_offset=52,
                        section_count=shnum,module_info_offset=found[0],elf_bytes=len(b),
                        hardware_verified=False)

def main():
    original=ROOT/'Star Ocean - First Departure (Japan).iso'
    previous=ROOT/'Star Ocean - First Departure (Korean Review 10).iso'
    assert sha(original)=='5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc'
    assert sha(previous)=='3dc5acf84ce56927199d2e9c14ead14aaed89305e88486febb96154766c9dbf7'
    a=Iso(original);b=Iso(previous)
    orig=a.read_entry(a.find('/PSP_GAME/SYSDIR/BOOT.BIN'))
    old=b.read_entry(b.find('/PSP_GAME/SYSDIR/BOOT.BIN'))
    elf,report=rebuild(orig,old)
    target=ROOT/'Star Ocean - First Departure (Korean Review 11 RC1).iso'
    assert not target.exists()
    shutil.copyfile(previous,target);changes=[]
    with target.open('r+b') as out:
        for name in ('BOOT.BIN','EBOOT.BIN'):
            entry=b.find('/PSP_GAME/SYSDIR/'+name)
            capacity=(entry.size+2047)//2048*2048
            assert len(elf)<=capacity
            # Never consume another file's sectors; require existing tail padding to be zero.
            b.f.seek(entry.lba*2048+entry.size)
            assert not any(b.f.read(capacity-entry.size))
            out.seek(entry.lba*2048);out.write(elf.ljust(capacity,b'\0'))
            changes.append((entry.lba*2048,capacity))
            for rec in entry.rec_offsets:
                out.seek(rec+10);out.write(struct.pack('<I',len(elf))+struct.pack('>I',len(elf)))
                changes.append((rec+10,8))
    a.close();b.close()
    # All other ISO bytes, including every translation/resource, must remain identical.
    with previous.open('rb') as src,target.open('rb') as dst:
        cursor=0
        for off,n in sorted(changes)+[(target.stat().st_size,0)]:
            assert off>=cursor
            while cursor<off:
                count=min(4*1024*1024,off-cursor)
                assert src.read(count)==dst.read(count);cursor+=count
            src.seek(n,1);dst.seek(n,1);cursor+=n
    check=Iso(target)
    for name in ('BOOT.BIN','EBOOT.BIN'):
        entry=check.find('/PSP_GAME/SYSDIR/'+name)
        assert entry.size==len(elf) and check.read_entry(entry)==elf
    check.close()
    delta=ROOT/'SO1_Korean_Review_11_RC1.xdelta';roundtrip=P/'roundtrip_review11.iso'
    assert not delta.exists() and not roundtrip.exists()
    subprocess.run([str(ROOT/'xdelta.exe'),'-e','-s',str(original),str(target),str(delta)],check=True)
    subprocess.run([str(ROOT/'xdelta.exe'),'-d','-s',str(original),str(delta),str(roundtrip)],check=True)
    report.update(iso_sha256=sha(target),patch_sha256=sha(delta),patch_bytes=delta.stat().st_size,
                  delta_roundtrip=sha(roundtrip)==sha(target),outside_executables_and_directory_sizes='IDENTICAL')
    assert report['delta_roundtrip'];roundtrip.unlink()
    q=P/'review11';q.mkdir(exist_ok=True)
    (q/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
