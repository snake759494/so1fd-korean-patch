"""Apply human-reviewed menu catalog ranges with explicit corrections."""
import json,sys,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
rows=json.loads((P/'review09/menu_audit_catalog.json').read_text(encoding='utf8'))
path=P/'menu_review09.json'
out=json.loads(path.read_text(encoding='utf8')) if path.exists() else {}
start,end=map(int,sys.argv[1:3])
corrections={}
for line in Path(sys.argv[3]).read_text(encoding='utf8').splitlines():
 if line.strip() and not line.startswith('#'):
  key,value=line.split('\t',1);corrections[int(key)]=value
assert all(start<=i<end for i in corrections)
for i in range(start,end):
 row=rows[i];value=corrections.get(i,row['ko'])
 if i not in corrections and row['jp'].endswith('LV') and row['jp'][:-2] in out:
  value=out[row['jp'][:-2]]+' LV'
 assert value!='CONTROL',(i,row)
 tags=r'\{[0-9a-f]+\}'
 assert re.findall(tags,row['jp'])==re.findall(tags,value),(i,'tags')
 source=re.split(tags,row['jp']);target=re.split(tags,value)
 for jp,ko in zip(source,target):
  if jp:out[jp]=ko
path.write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8')
print('Reviewed menu/table labels:',len(out))
