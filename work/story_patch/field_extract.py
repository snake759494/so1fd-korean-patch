from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/menu_patch/full_menu')]
import so1pack,slz,expand,extract
p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin')
def read(m):
 orig=p.read(m);chunks,types=expand.as_typed_chunks(orig);a,b=chunks[types.index(1)]
 blob=orig[a:b];chain=slz.parse_chain(blob);data=slz.decompress(blob)
 script=data[:chain[0][2]];font=data[chain[0][2]:]
 head=struct.unpack_from('<7I',script);table=head[0]+28;count=head[3];base=table+count*2
 assert base+head[4]==len(script),(m,head,base,len(script))
 offsets=list(struct.unpack_from(f'<{count}H',script,table))+[head[4]]
 assert offsets[0]==0 and offsets==sorted(offsets)
 c=next(c for c in extract.cat if c['member']==m and '/t1!' in c['path'])
 ids=extract.g['banks'][c['key']]['ids']
 rows=[{'index':i,'offset':base+o,'jp':extract.decode(script[base+o:base+offsets[i+1]],ids),'hex':script[base+o:base+offsets[i+1]].hex()} for i,o in enumerate(offsets[:-1])]
 return dict(member=m,orig=orig,a=a,b=b,blob=blob,chain=chain,script=script,font=font,head=head,table=table,base=base,offsets=offsets,rows=rows,ids=ids)
if __name__=='__main__':
 for m in map(int,sys.argv[1:]):
  r=read(m);(OUT/f'{m}.json').write_text(json.dumps(r['rows'],ensure_ascii=False,indent=1),encoding='utf8')
  print(m,len(r['rows']), '\n'.join(str(x['index'])+' '+x['jp'] for x in r['rows'][:8]))
