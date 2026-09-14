from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/menu_patch/full_menu')]
import tree,so1pack,slz,extract,expand
OUT=Path(__file__).parent
p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin')
rows=[]
for c in extract.cat:
 if '/t1!' not in c['path']:continue
 m=c['member'];u=(ROOT/f'work/unpack/{m//500:02}/{m:05}.bin').read_bytes()
 chunks,types=expand.as_typed_chunks(u)
 a,b=chunks[types.index(1)];n=tree.Node('raw',slz.decompress(u[a:b]))
 if not n:continue
 ids=extract.g['banks'][c['key']]['ids'];d=n.data[:c['hdr']]
 texts=[];off=0
 for b in d.split(b'\0'):
  if len(b)>=8:
   s=extract.decode(b,ids)
   if any(w in s for w in ['ラティ','ミリー','ドーン','クラトス','宇宙','ローク','自警','艦長']):texts.append([off,s])
  off+=len(b)+1
 if texts:rows.append({'member':m,'key':c['key'],'texts':texts})
(OUT/'survey.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1),encoding='utf8')
for r in rows:print(r['member'],str(r['texts'])[:700])
