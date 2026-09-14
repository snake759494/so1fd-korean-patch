"""Replace item-detail heading bitmaps, preserving every following icon resource."""
from pathlib import Path
import json,struct,hashlib
from PIL import Image,ImageDraw,ImageFont
import build_descriptions as b
P=b.P;ROOT=b.ROOT

def decode(blob,at):
 c,u=struct.unpack_from('<II',blob,at+4)
 data=b.fe.slz.decompress_payload(blob[at+16:at+16+c],blob[at+3],u)
 return data,b.tree.parse(data,'d'),c

def render(text,size,levels):
 font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),size)
 box=font.getbbox(text);w=max(4,((box[2]-box[0]+5)//4)*4)
 if w>220 or box[3]-box[1]>22:return None
 im=Image.new('L',(w,22));ImageDraw.Draw(im).text((1-box[0],(22-box[3]+box[1])//2-box[1]),text,font=font,fill=255)
 pixels=[round(round(v/255*(levels-1))*15/(levels-1)) for v in im.getdata()]
 packed=bytes(pixels[i]|(pixels[i+1]<<4) for i in range(0,len(pixels),2))
 return struct.pack('<HH',w,22)+packed

def preview(raw):
 w,h=struct.unpack_from('<HH',raw);im=Image.new('L',(w,h));im.putdata([v*17 for x in raw[4:] for v in (x&15,x>>4)]);return im

def main():
 orig=b.fe.p.read(3731);path=P/'members/member3731_korean.bin';before=path.read_bytes();out=bytearray(before)
 offsets=[at for at in range(0,len(orig),2048) if orig[at:at+3]==b'SLZ'];assert len(offsets)==1589
 sources={x['id']:x for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='table' and x['member']==3320}
 assert sources[3000]['jp']=='マジックカンバス' and sources[3489]['jp']=='ロングソード' and sources[3676]['jp']=='レザーアーマー'
 cache=b.load_cache();review=json.loads((P/'menu_review09.json').read_text(encoding='utf8'));report=[];errors=[]
 for i,at in enumerate(offsets):
  row=sources[3000+i];jp=row['jp'];ko=cache.get(b.norm(jp),jp)
  try:
   u,t,c=decode(before,at);title=b.tree.find(t,'d/0');ow,oh=struct.unpack_from('<HH',title.data);assert oh==22 and len(title.data)==4+ow*oh//2
   if b.JP.search(jp):assert b.norm(jp) in {b.norm(k) for k in review} and ko!=jp,(i,jp)
   _,_,oc=decode(orig,at);next_header=orig.find(b'SLZ',at+16+oc)
   limit=min(offsets[i+1] if i+1<len(offsets) else len(orig),next_header if next_header>=0 else len(orig))-at
   assert limit>=16+c
   if ko==jp and not b.JP.search(jp):
    report.append(dict(index=i,id=3000+i,offset=at,jp=jp,ko=ko,changed=False));continue
   chosen=None
   for size,levels in [(20,16),(20,4),(18,4),(18,2),(16,2),(14,2),(12,2)]:
    bitmap=render(ko,size,levels)
    if bitmap is None:continue
    rebuilt=b.mb.repack(t,{title.path:bitmap})
    mode,payload=min(((m,b.fe.slz.compress_payload(rebuilt,m)) for m in (1,2)),key=lambda x:len(x[1]))
    if len(payload)+16<=limit:
     chosen=bitmap,rebuilt,mode,payload,size,levels;break
   assert chosen is not None,(i,jp,ko,'heading exceeds allocated slot',limit)
   bitmap,rebuilt,mode,payload,size,levels=chosen
   allocated=max(c,len(payload));assert not any(before[at+16+c:at+16+allocated])
   patch=b'SLZ'+bytes([mode])+struct.pack('<III',allocated,len(rebuilt),0)+payload.ljust(allocated,b'\0')
   assert b.fe.slz.decompress(patch)==rebuilt
   rt=b.tree.parse(rebuilt,'d')
   for node in ('d/1','d/2'):assert b.tree.find(rt,node).data==b.tree.find(t,node).data
   out[at:at+len(patch)]=patch
   report.append(dict(index=i,id=3000+i,offset=at,jp=jp,ko=ko,changed=True,font_size=size,levels=levels,width=struct.unpack_from('<H',bitmap)[0],bitmap_sha256=hashlib.sha256(bitmap).hexdigest(),slot_bytes=limit,used_bytes=len(payload)+16))
  except Exception as e:errors.append(dict(index=i,offset=at,error=repr(e)))
  if (i+1)%200==0:print(i+1,'errors',len(errors),flush=True)
 # Only aligned title resources may differ: all icon data and inter-resource padding remain exact.
 cursor=0
 for r in report:
  at=r['offset'];assert before[cursor:at]==out[cursor:at]
  _,_,c=decode(out,at);cursor=at+16+c
 assert before[cursor:]==out[cursor:]
 result=dict(rows=len(offsets),success=report,errors=errors,source_sha256=hashlib.sha256(before).hexdigest(),member_sha256=hashlib.sha256(out).hexdigest(),icon_bytes_preserved=True)
 (P/'review09/item_title_build_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf8')
 print('DONE',len(report),len(errors),errors[:10],flush=True)
 assert not errors
 path.write_bytes(out)
 examples=[r for r in report if r.get('changed')][:24]+[r for r in report if r['ko'] in ('플레어 봄','리저렉트 보틀','롱소드','레더 아머')]
 sheet=Image.new('RGB',(600,len(examples)*34),(20,25,40));draw=ImageDraw.Draw(sheet)
 for y,r in enumerate(examples):
  _,t,_=decode(out,r['offset']);im=preview(b.tree.find(t,'d/0').data)
  sheet.paste((255,255,255),(110,y*34),im);draw.text((4,y*34+7),str(r['id']),fill='white')
 sheet.save(P/'review09/item_titles_korean.png')
if __name__=='__main__':main()
