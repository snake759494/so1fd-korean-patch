from pathlib import Path
import sys,struct,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'work/tools'));sys.path.insert(0,str(Path(__file__).parent))
import so1pack,slz,tree,fieldbank
from extract import g,decode
OUT=Path(__file__).parent
def font_ids(data,f):
 inv={b:i for i,b in enumerate(g['glyphs'])}
 return [inv.get(data[f['bitmaps']+i*24:f['bitmaps']+(i+1)*24],-1) for i in range(f['count'])]
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');d=p.read(3731);rows=[];off=0
 while True:
  off=d.find(b'SLZ',off)
  if off<0:break
  at=off;off+=3
  if at+16>len(d):continue
  mode=d[at+3];comp,unp,nxt=struct.unpack_from('<III',d,at+4)
  if mode>2 or unp<64 or unp>20000 or at+16+comp>len(d):continue
  try:
   u=slz.decompress_payload(d[at+16:at+16+comp],mode,unp)
   fs=fieldbank.fonts(u)
   if not fs:continue
   f=fs[-1];ids=font_ids(u,f);t=tree.parse(u,'d')
   desc=tree.find(t,'d/1')
   if desc and len(desc.data)>4 and desc.data[:4]==b'\x04\0\0\0':
    b=desc.data[4:].split(b'\0')[0]
    rows.append({'offset':at,'mode':mode,'comp':comp,'unp':unp,'next':nxt,'font':f,'text':decode(b,ids),'hex':b.hex(),'path':desc.path})
  except Exception:continue
 (OUT/'item_descriptions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1),encoding='utf8')
 print('descriptions',len(rows));print('\n'.join(str(r['offset'])+' '+r['text'] for r in rows if any(s in r['text'] for s in ['1メートル','木で作','動物の皮','木を','好んで着'])))
if __name__=='__main__':main()
