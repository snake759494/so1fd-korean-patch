"""Conservative screen-width candidates; actual rendering is a separate check."""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from tagged_dialogue import reflow,restore_waits
c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
t=json.loads((P/'message_translations.json').read_text(encoding='utf8'))
from name_encoding import NAMES
names=[x[1] for x in NAMES]
out=[]
for x in c:
 s=reflow(x['jp'],restore_waits(x['jp'],t[str(x['id'])]))
 s=re.sub(r'\{8c80([0-9a-f]{2})\}',lambda m:names[int(m[1],16)] if int(m[1],16)<14 else '',s)
 lines=[re.sub(r'\{[0-9a-f]+\}','',z) for z in re.split(r'\{(?:8080|8180|8280)\}',s)]
 n=max(map(len,lines),default=0)
 if n>34:out.append(dict(id=x['id'],max_cells=n,lines=lines))
(P/'review09/width_candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8')
print('Candidates:',len(out))
print(json.dumps(sorted(out,key=lambda x:-x['max_cells'])[:25],ensure_ascii=False,indent=1))
