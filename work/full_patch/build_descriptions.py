from font_bank import *
import tree,build as mb,nested
def main():
 orig=fe.p.read(3731);out=bytearray((ROOT/'work/menu_patch/full_menu/member3731_korean.bin').read_bytes());cache=load_cache()
 from patch_descriptions import DESCS
 reviewed=json.loads((P/'description_review09.json').read_text(encoding='utf8'))
 control_file=P/'description_control_review09.json'
 controlled=json.loads(control_file.read_text(encoding='utf8')) if control_file.exists() else {}
 sources={x['id']:x['jp'] for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='description'}
 rows=json.loads((ROOT/'work/menu_patch/full_menu/item_descriptions.json').read_text(encoding='utf8'));good=[];bad=[]
 for row in rows:
  at=row['offset']
  if at in DESCS and re.sub(r'^(?:\{[0-9a-f]+\})+','',sources[at]) not in reviewed and str(at) not in controlled:good.append(at);continue
  try:
   mode=orig[at+3];comp,unp,nxt=struct.unpack_from('<III',orig,at+4);assert nxt==0
   u=fe.slz.decompress_payload(orig[at+16:at+16+comp],mode,unp);t=tree.parse(u,'d');fnode=tree.find(t,'d/2');text=tree.find(t,'d/1')
   from description_ids import font_ids
   ids=font_ids(u,row['font']);raw=bytes.fromhex(row['hex']);seg=translate(raw,ids,cache)
   if str(at) in controlled:
    target=controlled[str(at)];assert target['jp']==sources[at]
    seg=[('raw',bytes.fromhex(s[1:-1]),None) if s.startswith('{') else ('ko',b'',s) for s in re.findall(r'\{[0-9a-f]+\}|[^{}]+',target['ko'])]
    original_text=[bb for kind,bb,s in parts(raw,ids,field=False) if kind=='text']
    assert sum(kind=='ko' for kind,bb,s in seg)==len(original_text),(at,'description segment mismatch')
    text_iter=iter(original_text)
    seg=[(kind,next(text_iter),s) if kind=='ko' else (kind,bb,s) for kind,bb,s in seg]
    expected=[bb for kind,bb,v in tokens(raw,ids,{}) if kind=='control' and v!=0x4000]
    actual=[bb for kind,bb,v in tokens(b''.join(bb for kind,bb,s in seg if kind=='raw'),ids,{}) if kind=='control']
    assert actual==expected,(at,'description control mismatch')
   if seg is None:
    assert not JP.search(sources[at]),(at,'untranslated description')
    good.append(at);continue
   font,newraw=remake(fnode.data,{0:raw},{0:seg},reserve=0,trim=True)
   if str(at) in controlled:
    n=struct.unpack_from('<I',font)[0]
    assert [bb for kind,bb,v in tokens(newraw[0],list(range(n)),{}) if kind=='control']==[bb for kind,bb,v in tokens(raw,ids,{}) if kind=='control'],(at,'built description controls changed')
   inner=mb.repack(t,{fnode.path:font,text.path:struct.pack('<I',4)+newraw[0]+b'\0'})
   md,payload=min(((md,fe.slz.compress_payload(inner,md)) for md in [1,2]),key=lambda x:len(x[1]));size=max(comp,len(payload))
   next_header=orig.find(b'SLZ',at+16+comp)
   limit=min(max(2048,16+comp),next_header-at if next_header>=0 else len(orig)-at)
   if size+16>limit:raise ValueError(('description slot overflow',size+16,limit))
   assert not any(orig[at+16+comp:at+16+size])
   patch=b'SLZ'+bytes([md])+struct.pack('<III',size,len(inner),0)+payload.ljust(size,b'\0');assert fe.slz.decompress(patch)==inner
   out[at:at+len(patch)]=patch;good.append(at)
  except Exception as e:bad.append(dict(offset=at,error=repr(e)))
  if (len(good)+len(bad))%100==0:print(len(good),len(bad),flush=True)
 assert len(out)==len(orig);(P/'members/member3731_korean.bin').write_bytes(out)
 (P/'description_build_report.json').write_text(json.dumps(dict(success=good,errors=bad),ensure_ascii=False,indent=1),encoding='utf8');print('DONE',len(good),len(bad),bad[:3],flush=True)
if __name__=='__main__':main()
