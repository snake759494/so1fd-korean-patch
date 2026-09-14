"""Package the reviewed patch only after build and runtime evidence is recorded."""
from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def read(name):return json.loads((P/name).read_text(encoding='utf8'))
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def main():
 v=read('validation.json');runtime=read('review09/runtime09_report.json')
 assert v['delta_roundtrip']=='PASS' and v['outside_patched_ranges']=='IDENTICAL'
 assert digest(v['iso'])==v['sha256']
 assert runtime['release_smoke_pass'] and runtime['final_iso_sha256']==v['sha256']
 for name in ('menu_validation','description_validation','item_title_build_report'):
  assert not read(f'review09/{name}.json')['errors']
 assert not read('review09/menu_validation.json')['unreviewed_segments']
 field=read('field_build_report.json');assert len(field['success'])==974 and not field['errors']
 quality=dict(version='Korean Review 09',reviewed_unique_dialogues=8730,reviewed_colored_dialogues=2113,
  reviewed_unique_menu_table_strings=2484,reviewed_unique_descriptions=1175,description_rows=1589,
  item_title_images_audited=1589,item_title_images_changed=sum(x['changed'] for x in read('review09/item_title_build_report.json')['success']),
  field_banks=974,field_rows=sum(x['translated'] for x in field['success']),menu_banks=16,table_rows=3559,
  default_korean_character_names=14,subtitle_movies=7,subtitle_cues=93,
  iso_sha256=v['sha256'],full_game_all_routes_playtested=False,runtime_report='runtime09_report.json')
 (P/'review09/coverage09.json').write_text(json.dumps(quality,ensure_ascii=False,indent=1),encoding='utf8')
 readme=f'''# 스타 오션 First Departure 한글패치 — 검수 09

일본판 PSP용 한글 번역 검수본입니다.

대사 8,730종(색상 대사 2,113종 포함), 메뉴·공통표 2,484종,
설명문 1,175종을 검수했습니다. 실제 데이터에는 중복 대사와 설명도 반영했습니다.
아이템 상세 화면의 큰 이름 이미지 1,589개를 목록 이름과 대조해 한글화했습니다.
라티크스 등 14명의 기본 이름, 인물·지명 표기, 필살기·작전·아이템명,
능력치 효과 설명을 정리했습니다. 영상 7개의 자막 93개를 포함합니다.
이름을 직접 바꾸는 가나·영문 입력 기능과 일본어 음성은 유지합니다.

## 적용

수정되지 않은 일본판 ISO에 SO1_Korean_Review_09.xdelta를 적용하세요.
이전 한글판 ISO에 덧씌우는 패치가 아닙니다.

원본 SHA-256:
5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc

완성 ISO 파일명: {Path(v['iso']).name}
완성 ISO SHA-256: {v['sha256']}

xdelta UI에서 Patch는 동봉한 xdelta, Source File은 원본 일본판,
Output File은 새 ISO 경로로 지정합니다. ZIP에는 게임 ISO가 들어 있지 않습니다.

## 검증 범위

필드 974개, 메뉴 16개, 공통표 3개, 설명문 1,589행의 빌드 검사 통과.
메뉴·공통표 8,713행과 설명문 1,589행은 실제 글꼴 비트맵 및 제어 코드를
검수된 입력과 대조했습니다. 이벤트·색상·변수·음성·대기 명령을 보존했습니다.
xdelta를 원본에 적용한 결과가 위 ISO와 정확히 일치합니다.

PPSSPP 실행 확인의 구체적인 항목은 runtime09_report.json에 기록했습니다.
모든 동료 조합·분기·엔딩을 끝까지 플레이한 검증은 아닙니다.
14명 이름 표시 시험에는 임시 메모리로 이름 입력창을 바꾼 글꼴 시험도 포함됩니다.
사용자가 직접 바꾼 이름은 자동으로 개명하지 않습니다.
이전 일본어 기본 이름은 게임 표시 경로에서 한글로 변환합니다.
이전 버전의 상태 저장에는 과거 코드와 글꼴이 들어 있을 수 있으므로,
검증한 새 실행 파일을 사용하려면 게임을 재시작한 뒤 일반 저장을 불러오세요.
'''
 (P/'review09/README09.md').write_text(readme,encoding='utf8')
 files={
  'README.md':P/'review09/README09.md','SO1_Korean_Review_09.xdelta':P/'SO1_Korean_Review_09.xdelta',
  'validation.json':P/'validation.json','coverage09.json':P/'review09/coverage09.json',
  'runtime09_report.json':P/'review09/runtime09_report.json',
  'menu_validation.json':P/'review09/menu_validation.json','description_validation.json':P/'review09/description_validation.json',
  'item_title_build_report.json':P/'review09/item_title_build_report.json',
  'LICENSES/FONT_CREDITS.md':P/'review09/FONT_CREDITS.md',
  'LICENSES/Galmuri-OFL-1.1.md':ROOT/'work/publish/so1fd-korean-patch/LICENSES/Galmuri-OFL-1.1.md',
  'CHARACTER_REFERENCE.md':P/'review09/CHARACTER_REFERENCE.md'}
 for name in ('message_translations.json','menu_review09.json','description_review09.json','description_control_review09.json','terminology_review09.json'):
  files['translations/'+name]=P/name
 for path in sorted((P/'review09').glob('*.tsv')):files['reviews/'+path.name]=path
 for name in ('runtime_before_layout.json','layout_only_build_diff.json','battle_only_build_diff.json','battle_hook_build_diff.json','battle_name_font_report.json','name_executable_report.json'):
  files['validation/'+name]=P/'review09'/name
 for name in runtime.get('screenshots',[]):
  path=P/'review09'/name;assert path.exists();files['screenshots/'+path.name]=path
 target=ROOT/'SO1_Korean_Review_09_Patch.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,path in files.items():z.write(path,name)
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 result=dict(zip=str(target),zip_bytes=target.stat().st_size,zip_sha256=digest(target),iso=v['iso'],iso_sha256=v['sha256'])
 (P/'review09/release09_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf8')
 print(json.dumps(result,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
