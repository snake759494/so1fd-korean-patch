from pathlib import Path
import json,zipfile,hashlib,shutil
P=Path(__file__).resolve().parent;Q=P/'review10';ROOT=P.parents[1]
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 v=load(P/'validation.json');rt=load(Q/'runtime10_report.json');assert 'Review 10' in v['iso'] and v['delta_roundtrip']=='PASS';assert sha(Path(v['iso']))==v['sha256']==rt['iso_sha256'];assert rt['levelup_names_passed']==['라티크스','밀리','돈']
 assert not load(P/'review09/menu_validation.json')['errors'];assert not load(Q/'name_table_validation.json')['errors']
 readme=f'''# 스타 오션 First Departure 한글패치 검수 10

09판에서 발견된 전투 후 레벨업 이름 깨짐을 수정했습니다.
레벨업 문장에 들어가는 이름 코드가 일본어 한자 칸을 가리키던 문제입니다.
공통 메시지 글꼴 3개에 14명 이름을 반영했고 기존 문구의 글자 모양과 제어 코드를 보존했습니다.
실제 레벨업에서 라티크스, 밀리, 돈을 확인했습니다. 14명 전체는 3개 글꼴의 42개 이름 조합을 바이너리 검사했습니다.

## 사용
완성 ISO: {Path(v['iso']).name}
ISO SHA256: {v['sha256']}

동봉한 SO1_Korean_Review_10.xdelta는 수정되지 않은 일본판 원본 ISO에 적용하세요.
원본 SHA256: 5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc
이전 한글 ISO에 덧씌우지 마세요. ZIP에는 게임 ISO가 없습니다.

PPSSPP에서 게임을 완전히 종료한 뒤 10판 ISO를 여세요.
이전 상태 저장에는 과거 실행 코드와 글꼴이 남아 있으므로 일반 게임 저장으로 이어 하세요.

## 검증
원본 적용 xdelta 왕복 일치, 필드 974개 구조 검사, 메뉴·공통표 8,713행 글꼴 및 제어 코드 대조 통과.
레벨업 시험은 독립 시험용 PPSSPP에서 기존 테스트 상태를 불러온 뒤 새 전투 자원을 로드해 수행했습니다.
새 문구·글꼴 데이터 전체가 ISO 자원과 일치함을 메모리에서 확인했습니다.
시험 상태에 남아 있는 구버전 실행 코드 때문에 시험 사진 상단 HUD에는 영문 이름이 보일 수 있습니다.
이번 변경은 실행 코드를 바꾸지 않았으며, 09판에서 새 게임으로 확인한 한글 HUD 코드는 그대로입니다.

09판 기본 번역 및 초기 실행 검증 기록도 함께 포함합니다. 모든 분기·엔딩을 완주한 검증은 아닙니다.
'''
 (Q/'README10.md').write_text(readme,encoding='utf8')
 target=ROOT/'SO1_Korean_Review_10_Patch.zip'
 with zipfile.ZipFile(ROOT/'SO1_Korean_Review_09_Patch.zip') as old,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
  for info in old.infolist():
   if info.filename in ('README.md','SO1_Korean_Review_09.xdelta','validation.json','menu_validation.json'):continue
   name='baseline09/'+info.filename if info.filename in ('coverage09.json','runtime09_report.json') else info.filename
   out.writestr(name,old.read(info.filename))
  for name,path in {'README.md':Q/'README10.md','SO1_Korean_Review_10.xdelta':P/'SO1_Korean_Review_10.xdelta','validation.json':P/'validation.json','menu_validation.json':P/'review09/menu_validation.json'}.items():out.write(path,name)
  for name in ('runtime10_report.json','name_table_validation.json','loaded_table_evidence.json','build_diff.json'):out.write(Q/name,'review10/'+name)
  for name in rt['screenshots']:out.write(Q/name,'review10/screenshots/'+name)
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 report=dict(iso=v['iso'],iso_sha256=v['sha256'],zip=str(target),zip_bytes=target.stat().st_size,zip_sha256=sha(target),runtime_levelup='PASS')
 (Q/'release10_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
