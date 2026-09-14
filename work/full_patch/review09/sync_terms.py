"""Reuse agreed, manually reviewed item/skill labels in menu translation cache."""
import collections,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
t=json.loads((P/'message_translations.json').read_text(encoding='utf8'))
terms=json.loads((P/'terminology_review09.json').read_text(encoding='utf8'))
labels=collections.defaultdict(lambda:collections.defaultdict(list))
pattern=r'\{848003\}([^{}]+)\{848000\}'
for row in c:
 source=re.findall(pattern,row['jp']);target=re.findall(pattern,t[str(row['id'])])
 if len(source)!=len(target):continue
 for jp,ko in zip(source,target):
  if not re.search(r'[\u3040-\u9fff]',jp):continue
  labels[jp][ko].append(row['id'])
report=[]
for jp,variants in labels.items():
 if len(variants)==1:ko=next(iter(variants))
 elif len({re.sub(r'\s+','',v) for v in variants})==1:
  ko=max(variants,key=lambda v:v.count(' '))
 else:raise ValueError(('conflicting reviewed terms',jp,dict(variants)))
 report.append(dict(jp=jp,ko=ko,review_ids=sorted(i for ids in variants.values() for i in ids),previous=terms.get(jp)))
 terms[jp]=ko
terms.update({'イヴィーナ':'이레나','ヴァドグープ':'바도그프','リヴォースタワー':'리보스 타워',
 'セーフハウス':'은신처','反リヴォース派':'반 리보스파','バイオ研究所':'바이오 연구소',
 '早口':'고속 영창','旧異種族':'구 이종족','ジュディーム':'주디움','?JEWELRY':'?보석'})
(P/'terminology_review09.json').write_text(json.dumps(terms,ensure_ascii=False,indent=1),encoding='utf8')
(P/'review09/term_sync_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
print('Synced reviewed labels:',len(report))
