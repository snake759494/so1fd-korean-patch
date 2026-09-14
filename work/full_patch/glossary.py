from build_fields import P,ROOT
import json,sys,re
def make():
 sys.path.insert(0,str(ROOT/'work/menu_patch/full_menu'))
 from translations import T
 rows=json.loads((P/'extras_source.json').read_text(encoding='utf8'));out={}
 for x in rows:
  if x['kind']=='menu' and x['id'] in T and '{' not in x['jp'] and '{' not in T[x['id']]:out[x['jp']]=T[x['id']]
 spells='''파이어 볼트|이럽션|익스플로드|아이스 니들|딥 프리즈|애시드 레인|노아|윈드 블레이드|소닉 세이버|푄|매그넘 토네이도|테타너스 윈드|선더 볼트|선더 스톰|리플렉션|선더 클라우드|포겟|스타라이트|메테오 스웜|서던 크로스|세븐스 스타|트랙터 빔|그레이브|어스 그레이브|록 레인|레이|라이트 크로스|스타 플레어|루나 라이트|운즈|블랙 세이버|섀도 볼트|섀도 플레어|딥 미스트|그렘린 레어|데몬스 게이트|익스팅션|다크 서클|프레스|그래비티 프레스|픽스 클라우드|리플렉션|워드 오브 데스|에너지 애로|블러드 스큐라|로스트 멘탈|힐|큐어 라이트|페어리 힐|큐어 올|페어리 라이트|레이즈 데드|안티도트|큐어 컨디션|헤이스트|딜레이|그로스|프로텍션|엔젤 페더|사일런스|커스|블레스|뉴트럴'''.split('|')
 for x in rows:
  if x['kind']=='table' and x['member']==1709 and 1000<=x['id']<=1062:out[x['jp']]=spells[x['id']-1000]
 battle={0:'전투 결과',1:'경험치',2:'폴',3:'전멸했다……',4:'소모 MP',5:'을(를) 얻었다.',6:'은(는)',7:'레벨이 올랐다.',8:'을(를) 배웠다.',9:'백 어택',10:'포위 공격',11:'MP가 부족하다.',12:'디스크 덮개가 열려 있습니다.',13:'디스크에서 데이터를 읽을 수 없습니다.',14:'주문을 잊었다!',15:'영창할 수 없다!',16:'음성 데이터 오류가 발생했습니다.',17:'기습 공격',18:'방어 실패……!',19:'시간 초과…!',20:'땅',21:'물',22:'불',23:'바람',24:'번개',25:'별',26:'독',27:'빛',28:'어둠',29:'무',30:'에 약함',31:'에 강함',40:'반사',41:'소멸',42:'흡수됨',43:'흡수',44:'아군',45:'적',50:'스킬 포인트를 얻었다.',51:'주문 오류'}
 for x in rows:
  if x['kind']=='table' and x['member']==1709 and x['id'] in battle:out[x['jp']]=battle[x['id']]
 from translate_local import GLOSSARY
 out.update(GLOSSARY)
 out.update({'200フォル手に入れた。':'200폴을 얻었다.','もうやだよ…。':'이젠 싫어…','和むなぁ…。':'마음이 편안해지네…','「ぎょーざ…。 あっ、でもニンニクは抜いて…。':'「만두… 아, 마늘은 빼고…','「やっぱり肉まん。 ふかふかもちもち…。':'「역시 고기만두지. 폭신폭신하고 쫄깃쫄깃…','「美容にはツバメの巣…。 あ～ん♥':'「미용에는 제비집이 좋지… 아~앙♥'})
 (P/'reviewed_translations.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8');print(len(out))
if __name__=='__main__':make()
