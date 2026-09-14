"""Explicitly reviewed acquisition names; no machine output is promoted."""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from tagged_dialogue import reflow
names='''3918 링크 콤보
3951 레지스트 링
3960 천사상
3962 매지컬 필름
3999 빅토리얼 카드
4135 홀리 미스트
4184 전율의 그라탱
4185 부드러운 치즈 피자
4186 미소의 플라토
4187 비장의 고르곤
4223 조잡한 장식
4359 해물 스파게티
4368 스테이크 130
4371 스튜
4377 애플파이
4378 셔벗
4380 맥주
4485 달걀·유제품
4486 참치 대뱃살
4487 만년필
4488 페어리 미스트
4670 ?음식
4725 라운드 실드
4773 갓 짜낸 100%
5186 동인지…
5192 낡은 로드
5207 마음의 장벽
5311 리바이벌 카드
5362 기묘한 신발
5363 패럴라이즈 미스트
5416 볶음밥
5417 함박 스테이크
5418 달걀 프라이
5419 팔보채
5469 앵클릿
5470 호화로운 과일 모둠
5521 돼지고기 된장국
5649 마신류 어둠전골
5651 모털리얼 카드
5711 스미스 해머
5839 그림: 봄
5855 대지의 비밀
5856 루비 완드
5857 동인지♪
5871 슬픔의 반지
6083 투 핸드 소드
6261 리제너레이트 링
6263 레더 헬름
6305 프레시 시럽
6343 스모크 미스트
6368 어택 보틀
6373 헥사그램 카드
6417 스톤 체크
6429 라운델 대거
6430 발키리 오브
6432 미티어라이트
6438 미라주 로브
6439 고양이 슈트
6456 파인 실드
6510 피트 심벌
6769 카레의 왕자
6771 돌멩이
6777 대자연의 생명
6778 밴디드 헬름
7009 매지컬 로드
7010 엘븐 캡
7051 엘븐 보우
7063 ?장신구
7242 부츠
7243 쓴 주스
7323 츠바이핸더
7325 크로스보우
7326 플레이트 헬름
7327 나이츠 실드
7353 동인지!
7373 버서크 링
7478 향로
7567 에어 슬래시
7568 아르발레스트
7569 미스티 심벌
7570 아쿠아 링
7710 리저렉트 미스트
7799 엘븐 부츠
7800 테트라 봄
7801 몽라셰 DRC
7802 수박바
7803 내추럴 하이
7910 보물 상자
7955 아틀라스 링
7962 성스러운 지팡이 밀리언 테러
7963 드래곤 에지
7970 힐 링
7971 홀리 오브
7972 궁극 펀치
7979 카이저 너클
7982 인피니티 링
7983 페어리 링
7994 와이즈 링
7995 무라사마 블레이드
7996 시우스 스페셜
7999 오라 블레이드
8004 수정석
8006 현자의 돌
8007 리플렉션 링
8034 미스릴 그리브
8046 미스릴 헬름
8049 드림 크라운
8098 매지컬 항아리
8497 카미카제 토닉
8498 멘탈 포트
8615 롱 스피어
8616 인세인 링
8617 엘리먼트 에지'''
c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
t=json.loads((P/'message_translations.json').read_text(encoding='utf8'))
terms=json.loads((P/'terminology_review09.json').read_text(encoding='utf8'))
out={}
for line in names.splitlines():
 k,name=line.split(' ',1);jp=c[int(k)]['jp']
 m=re.fullmatch(r'\{8580\}\{848003\}(.+?)\{848000\}を手に入れた。\{8280\}',jp)
 assert m,k
 # Parenthesized particle handles Latin suffixes without guessing pronunciation.
 last=re.sub(r'[^가-힣]','',name)[-1]
 particle='을' if (ord(last)-0xac00)%28 else '를'
 if name.endswith(('130','100%','DRC')):particle={'130':'을','100%':'를','DRC':'를'}[next(x for x in ('130','100%','DRC') if name.endswith(x))]
 ko='{8580}{848003}'+name+'{848000}'+particle+' 얻었다.{8280}'
 reflow(jp,ko);out[k]=ko;terms[m[1]]=name
t.update(out)
(P/'message_translations.json').write_text(json.dumps(t,ensure_ascii=False,indent=1),encoding='utf8')
(P/'terminology_review09.json').write_text(json.dumps(terms,ensure_ascii=False,indent=1),encoding='utf8')
print('Reviewed item messages:',len(out),'total:',len(t))
