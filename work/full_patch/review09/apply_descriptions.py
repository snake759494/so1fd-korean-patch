"""Apply explicitly reviewed description text by original block offset."""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
rows={x['id']:x for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='description'}
path=P/'description_review09.json'
t=json.loads(path.read_text(encoding='utf8')) if path.exists() else {}
control_path=P/'description_control_review09.json'
control=json.loads(control_path.read_text(encoding='utf8')) if control_path.exists() else {}
for line in Path(sys.argv[1]).read_text(encoding='utf8').splitlines():
 if not line.strip() or line.startswith('#'):continue
 key,ko=line.split('\t',1);row=rows[int(key)]
 source=re.sub(r'^(?:\{[0-9a-f]+\})+','',row['jp'])
 if re.search(r'\{[0-9a-f]+\}',source):
  assert re.findall(r'\{[0-9a-f]+\}',row['jp'])==re.findall(r'\{[0-9a-f]+\}',ko),(key,'control mismatch')
  control[key]=dict(jp=row['jp'],ko=ko)
  continue
 t[source]=ko
path.write_text(json.dumps(t,ensure_ascii=False,indent=1),encoding='utf8')
control_path.write_text(json.dumps(control,ensure_ascii=False,indent=1),encoding='utf8')
print('Reviewed unique descriptions:',len(t)+len({x['jp'] for x in control.values()}))
