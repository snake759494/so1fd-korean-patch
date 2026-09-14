import sys,json,hashlib,struct
sys.path.insert(0,'work/full_patch');import build_name_fonts as n
report=[]
for m in (11,1708,2398):
 src=n.fe.p.read(m);root=n.tree.parse(src,str(m));leaf=n.tree.find(root,f'{m}!/3');data=bytearray(leaf.data);at=1496 if m!=2398 else 520
 old=bytes(data)
 for alias,ch in n.ALIASES.items():
  cell=ord(alias)-32;x=cell%32*8;y=cell//32*8
  for yy,bits in enumerate(n.PATTERNS[ch]):
   for xx,v in enumerate(bits):
    p=at+(y+yy)*128+(x+xx)//2;shift=((x+xx)%2)*4
    data[p]=(data[p]&~(15<<shift))|(15*int(v)<<shift)
 allowed={at+(16+y)*128+x for y in range(8) for x in range(4,100)}
 assert all(i in allowed for i,(a,b) in enumerate(zip(old,data)) if a!=b)
 n.tree.mark(root,leaf.path,bytes(data));out=n.tree.build(root);assert len(out)==len(src)
 path=n.P/f'members/member{m}_korean.bin';path.write_bytes(out)
 reread=n.tree.find(n.tree.parse(out,str(m)),leaf.path).data;assert reread==data
 report.append(dict(member=m,path=leaf.path,texture_offset=at,changed_bytes=sum(a!=b for a,b in zip(old,data)),sha256=hashlib.sha256(out).hexdigest()))
(n.P/'review09/battle_name_font_report.json').write_text(json.dumps(dict(success=report,errors=[]),indent=1))
print(report)
