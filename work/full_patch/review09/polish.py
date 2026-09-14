"""Small, explicit terminology and layout corrections to reviewed text."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from tagged_dialogue import reflow,restore_waits
c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
t=json.loads((P/'message_translations.json').read_text(encoding='utf8'))
changed={}
for k,v in t.items():
 n=v.replace('보물전','보물고')
 if k=='1367':n=n.replace('기사단장','기사장')
 if k=='1723':n=n.replace('도미 오렌지 소테','옥돔 오렌지 소테')
 if k=='2481':n=n.replace('술고약 100%','숙취 100%')
 if k=='2421':n=n.replace('{8d80} 버튼','{8d80}、 버튼')
 if k=='40':n=n.replace('보통은 도주를 선택하지 마세요.','전투 도주는 피하세요.')
 if k=='148':n='롤랜드 음원 SC-88Pro의 샘플 곡을 PS용으로 변환했습니다. 실시간 녹음이라 연주한 그대로일 겁니다.{8280}'
 if k=='149':n='관현악곡은 음량 변화가 크고 게임에 쓰지 않아 음량을 맞추지 않았습니다. 소리가 작으니 볼륨을 높여 주세요.{8280}'
 if v!=n:
  reflow(c[int(k)]['jp'],restore_waits(c[int(k)]['jp'],n));changed[k]={'before':v,'after':n}
for k,r in changed.items():t[k]=r['after']
(P/'message_translations.json').write_text(json.dumps(t,ensure_ascii=False,indent=1),encoding='utf8')
history=P/'review09'/'polish_changes.json'
old=json.loads(history.read_text(encoding='utf8')) if history.exists() else {}
old.update(changed);history.write_text(json.dumps(old,ensure_ascii=False,indent=1),encoding='utf8')
terms=json.loads((P/'terminology_review09.json').read_text(encoding='utf8'))
terms.update({'宝物殿':'보물고','騎士長':'기사장','騎士団長':'기사단장','甘鯛のオレンジソテー':'옥돔 오렌지 소테','わるよい100%':'숙취 100%'})
(P/'terminology_review09.json').write_text(json.dumps(terms,ensure_ascii=False,indent=1),encoding='utf8')
print('Polished:',len(changed))
