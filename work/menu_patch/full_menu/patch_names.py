from build import *
# Each alias is only substituted by display hooks; save/name data stays Japanese.
ALIASES={'Q':'라','J':'티','Y':'밀','Z':'리',';':'돈'}

def patch_fonts():
 reports=json.loads((OUT/'build_report.json').read_text(encoding='utf8'))
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin')
 for m in sorted(set(int(k.split(':')[0]) for k in T)-{2346}):
  if sys.argv[1:] and str(m) not in sys.argv[1:]:continue
  path=OUT/f'member{m}_korean.bin';source=path.read_bytes();root=parse_resource(source,m);font=bytearray(tree.find(root,f'{m}!/1').data);n,h=struct.unpack_from('<II',font)
  group=tree.find(root,f'{m}!/0/1');strings=group.data.split(b'\0')
  # Redirect the name conversion table, reusing translated Korean glyphs when available.
  rep=next((r for r in reports if r['member']==m),{'mapping':{}});mapping=dict(rep['mapping']);widths=bytearray(font[8:8+n]);glyphs=bytearray(font[8+n:8+n+n*24])
  for alias,ch in ALIASES.items():
   v=mapping.get(ch)
   if not v:
    n+=1;v=n;mapping[ch]=v;widths.append(12);b=kfont.encode(kfont.render(ch));glyphs+=b''.join(b[j:j+2][::-1] for j in range(0,24,2))
   strings[45 if alias==';' else ord(alias)-64]=enc(v)
  replacements={group.path:b'\0'.join(strings),f'{m}!/1':struct.pack('<II',n,12)+widths+glyphs};inner=repack(root.kids[0],replacements)
  candidates=[(mode,slz.compress_payload(inner,mode)) for mode in [1,2]];mode,payload=min(candidates,key=lambda x:len(x[1]))
  assert len(payload)+16<=len(source),(m,len(payload),len(source))
  patch=(b'SLZ'+bytes([mode])+struct.pack('<III',len(payload),len(inner),0)+payload).ljust(len(source),b'\0')
  assert slz.decompress(patch)==inner;path.write_bytes(patch);print('name glyphs',m,n,'payload',len(payload),flush=True)

def main():patch_fonts()
if __name__=='__main__':main()
