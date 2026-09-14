"""Keep colored item labels equal to the reviewed menu label for the same JP source."""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from translate_local import norm
from canonical_names import canonicalize
menu=json.loads((P/'menu_review09.json').read_text(encoding='utf8'))
lookup={norm(k):canonicalize(v) for k,v in menu.items()}
catalog=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
path=P/'message_translations.json';targets=json.loads(path.read_text(encoding='utf8'))
pattern=r'\{848003\}([^{}]+)\{848000\}'
report=[]
for row in catalog:
 key=str(row['id']);jp=re.findall(pattern,row['jp']);ko=list(re.finditer(pattern,targets[key]))
 assert len(jp)==len(ko)
 for source,match in reversed(list(zip(jp,ko))):
  label=lookup.get(norm(source));old=match.group(1)
  if not label or label==old:continue
  a,b=match.span(1);s=targets[key];end=match.end();suffix=s[end:]
  # A changed final consonant can change the immediately following particle.
  if '\uac00'<=label[-1]<='\ud7a3' and old and '\uac00'<=old[-1]<='\ud7a3':
   jong=(ord(label[-1])-0xac00)%28
   for pair in [('으로','로'),('은','는'),('이','가'),('을','를'),('과','와')]:
    found=next((p for p in pair if suffix.startswith(p)),None)
    if found:
     particle=pair[0] if jong and not(pair[0]=='으로' and jong==8) else pair[1]
     suffix=particle+suffix[len(found):];break
  targets[key]=s[:a]+label+s[b:end]+suffix
  report.append(dict(id=row['id'],jp=source,previous=old,reviewed=label))
path.write_text(json.dumps(targets,ensure_ascii=False,indent=1),encoding='utf8')
(P/'review09/menu_dialogue_sync_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
print('Synced colored item labels:',len(report))
