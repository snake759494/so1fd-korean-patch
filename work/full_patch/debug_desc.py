from build_descriptions import *
from description_ids import font_ids
from description_overrides import T
cache=load_cache();orig=fe.p.read(3731)
rows=json.loads((ROOT/'work/menu_patch/full_menu/item_descriptions.json').read_text(encoding='utf8'))
for r in rows:
 if r['offset'] not in T:continue
 at=r['offset'];comp,unp,nxt=struct.unpack_from('<III',orig,at+4)
 u=fe.slz.decompress_payload(orig[at+16:at+16+comp],orig[at+3],unp)
 print(at,comp,translate(bytes.fromhex(r['hex']),font_ids(u,r['font']),cache))
 print('next',orig.find(b'SLZ',at+16+comp)-at)
