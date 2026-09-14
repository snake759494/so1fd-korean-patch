from pathlib import Path
import sys,json,re,collections,traceback
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/story_patch'))
import field_extract as fe
from codec import decode
from build_fields import labels
def main():
 rows=[];errors=[];banks=[]
 members=sorted(set(c['member'] for c in fe.extract.cat if '/t1!' in c['path']))
 for m in members:
  try:
   r=fe.read(m)
   for x in r['rows']:
    x['jp']=decode(bytes.fromhex(x['hex']),r['ids'],labels)
    rows.append(dict(member=m,**x))
   banks.append({'member':m,'strings':len(r['rows']),'font':len(r['ids'])})
  except Exception as e:errors.append({'member':m,'error':repr(e)})
  if m%50==0:print(m,len(rows),'rows',flush=True)
 (OUT/'field_original.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1),encoding='utf8')
 groups=collections.defaultdict(list)
 for x in rows:
  s=re.sub(r'^\d{5}','',x['jp']);groups[s].append([x['member'],x['index']])
 unique=[{'id':i,'jp':s,'locations':loc} for i,(s,loc) in enumerate(groups.items())]
 (OUT/'field_unique.json').write_text(json.dumps(unique,ensure_ascii=False,indent=1),encoding='utf8')
 (OUT/'field_readable.json').write_text(json.dumps(unique,ensure_ascii=False,indent=1),encoding='utf8')
 report={'field_banks':len(banks),'field_strings':len(rows),'unique_strings':len(unique),'unique_characters':sum(len(x['jp']) for x in unique),'banks':banks,'errors':errors}
 (OUT/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
 print({k:v for k,v in report.items() if k!='banks'},flush=True)
if __name__=='__main__':main()
