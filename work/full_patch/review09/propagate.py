"""Reuse reviewed identical messages across layout-only source variations."""
import sys,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from tagged_dialogue import reflow,restore_waits
c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
t=json.loads((P/'message_translations.json').read_text(encoding='utf8'))
proofpath=P/'review09/equivalent_reviews.json'
proof=json.loads(proofpath.read_text(encoding='utf8')) if proofpath.exists() else {}
def key(jp):return re.sub(r'\s+','',''.join(jp.split('{8080}')))
known={}
for row in c:
 i=str(row['id'])
 if i not in t:continue
 known.setdefault(key(row['jp']),[]).append(i)
count=0
for row in c:
 i=str(row['id'])
 if i in t:continue
 matches=known.get(key(row['jp']),[])
 if not matches:continue
 # Conflicting prior choices should be inspected, never selected arbitrarily.
 targets={restore_waits(c[int(k)]['jp'],t[k]).replace('{8080}','') for k in matches}
 if len(targets)!=1:continue
 ko=targets.pop()
 try:reflow(row['jp'],ko)
 except ValueError:continue
 t[i]=ko;proof[i]={'reviewed_source_id':int(matches[0]),'method':'identical Japanese and non-newline controls; layout reflow only'};count+=1
(P/'message_translations.json').write_text(json.dumps(t,ensure_ascii=False,indent=1),encoding='utf8')
proofpath.write_text(json.dumps(proof,ensure_ascii=False,indent=1),encoding='utf8')
print('Equivalent layout variants:',count,'total:',len(t))
