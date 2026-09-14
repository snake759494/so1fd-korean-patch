"""Apply user-specified spellings to authored targets without changing source keys."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from name_encoding import NAMES
replacements={'라틱스':'라티크스','로니키스':'로닉스','애슐리':'아슈레이','제랜드':'제란드','아르카나':'알카나','워런':'워렌',
 '라이아스':'라이어스','무어':'무아','오타님':'오터님','메토크스':'메토쿠스','파지 신전':'퍼지 신전',
 '트로프':'트롭','에크다트':'엑더트','두르스':'둘스','파게트':'파겟','이비나':'이레나','베이즈':'베이스',
 '칼나스':'카르나스','진홍의 방패':'붉은 방패','구이종족':'구 이종족','키리트':'킬리트'}
def fix(s):
 for a,b in replacements.items():s=s.replace(a,b)
 return s
from canonical_names import REPLACEMENTS as replacements, canonicalize as fix
changed={}
for name in ['message_translations.json','terminology_review09.json','description_review09.json','reviewed_translations.json','name_transliterations.json']:
 path=P/name
 if not path.exists():continue
 data=json.loads(path.read_text(encoding='utf8'));n=0
 for k,v in data.items():
  if isinstance(v,str) and fix(v)!=v:data[k]=fix(v);n+=1
 if name=='message_translations.json':
  for line in (P/'review09/character_context_fixes.tsv').read_text(encoding='utf8').splitlines():
   key,value=line.split('\t',1)
   if data.get(key)!=value:data[key]=value;n+=1
 path.write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf8');changed[name]=n
(P/'review09/user_name_policy.json').write_text(json.dumps(dict(names=[dict(original=jp,display=short,full=full) for jp,short,full in NAMES],other_names=['아스모데우스','지에 리보스'],replacements=replacements,changed=changed),ensure_ascii=False,indent=1),encoding='utf8')
print(changed)
