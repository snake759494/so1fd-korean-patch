"""Apply explicitly authored full-message reviews, preserving speaker/end tokens."""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from tagged_dialogue import reflow,restore_waits

def apply(file):
 c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
 t=json.loads((P/'message_translations.json').read_text(encoding='utf8'))
 out={}
 for line in Path(file).read_text(encoding='utf8').splitlines():
  if not line.strip() or line.startswith('#'):continue
  key,ko=line.split('\t',1);jp=c[int(key)]['jp']
  if ko.startswith('@'):ko=re.match(r'^\{8c80[0-9a-f]{2}\}「',jp).group()+ko[1:]
  if jp.endswith('{8280}') and not ko.endswith('{8280}'):ko+='{8280}'
  try:reflow(jp,restore_waits(jp,ko))
  except Exception as e:raise ValueError((key,str(e))) from e
  assert key not in out,key
  out[key]=ko
 t.update(out)
 (P/'message_translations.json').write_text(json.dumps(t,ensure_ascii=False,indent=1),encoding='utf8')
 print('Reviewed:',len(out),'total:',len(t))

if __name__=='__main__':apply(sys.argv[1])
