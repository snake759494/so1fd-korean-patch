from build_fields import *
import zipfile,shutil
v=json.loads((P/'validation.json').read_text(encoding='utf8'))
field=json.loads((P/'field_build_report.json').read_text(encoding='utf8'))
menus=json.loads((P/'menu_build_report.json').read_text(encoding='utf8'))
catalog=json.loads((P/'segment_catalog.json').read_text(encoding='utf8'));cache=load_cache()
hand={int(line.split('\t',1)[0]) for f in (P/'hand_translations').glob('*.tsv') for line in f.read_text(encoding='utf8').splitlines() if line.strip()}
(P/'translation_review.json').write_text(json.dumps([dict(id=x['id'],jp=x['jp'],ko=cache.get(x['jp']),manual_tsv=x['id'] in hand) for x in catalog],ensure_ascii=False,indent=1),encoding='utf8')
quality=dict(version='08 draft',reviewed_whole_messages=len(json.loads((P/'message_translations.json').read_text(encoding='utf8'))),catalog_segments=len(catalog),manual_segments=len(hand),missing_segments=[x['id'] for x in catalog if x['jp'] not in cache],japanese_in_translated_segments=[x['id'] for x in catalog if JP.search(cache.get(x['jp'],''))],field_banks=len(field['success']),field_rows_translated=sum(x['translated'] for x in field['success']),field_rows_total=sum(x['total'] for x in field['success']),new_menu_rows=sum(x['translated'] for x in menus),table_rows=3559,description_rows=1396,movie_subtitles=93,movies=7,unresolved=['Most dialogue remains machine translated and needs manual review','Battle HUD character names not confirmed translated','Choice layout and long-line wrapping not fully audited','Full-game runtime progression not tested','OCR source transcription may contain errors'],screenshots='12 user screenshots included as before references; these are not screenshots of Draft08')
(P/'coverage.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf8')
screens=P/'screens_before';screens.mkdir(exist_ok=True)
for i in range(0,12):
 src=Path('D:/psp/ppsspp_win/memstick/PSP/SCREENSHOT')/f'ULJM05290_{i:05}.jpg'
 if src.exists():shutil.copyfile(src,screens/src.name)
readme=f'''# 스타오션 First Departure 한국어 전체 데이터 초안 08

완전 감수판이 아닙니다. 전체 추출 데이터에 기계 번역과 일부 직접 번역을 적용한 시험 빌드입니다.
원본 일본판 및 정상 동작을 확인한 Story06 ISO는 그대로 보존했습니다.

## 08 수정 사항
- 색상 전환을 번역 경계로 삼지 않는 문장 단위 감수 경로 추가.
- 초반의 색상 강조 대사 139개를 문장 전체로 직접 재번역.
- 필드 대기 명령의 2바이트 값을 보존하고, 메뉴의 1바이트 형식과 구분.
- 띄어쓰기 단위 줄바꿈 개선 및 직접 감수 번역 추가.
- 공통 기호 슬롯 1–260을 보존하여 괄호·따옴표와 한글 슬롯의 충돌 방지.
- 전체 색상 강조 메시지 2,113개 중 나머지 1,974개는 문장 단위 감수가 남아 있음.

## 적용 범위
- 지도 대사 974개 묶음: {quality['field_rows_translated']:,}개 행에 번역 적용(중복 포함).
- 메뉴 16개 묶음: 기존 메뉴 번역을 유지하고 {quality['new_menu_rows']:,}개 행 추가 적용.
- 공용 문자열 3,559개, 아이템·스킬 설명 1,396개.
- 자막 영상 총 7개, 자막 93개. 음성은 일본어 원본 유지.
- 고유 번역 조각 {len(catalog):,}개 중 직접 검토한 TSV 항목 {len(hand):,}개.

## 남은 작업과 제한
대부분의 대사는 기계 번역 초안으로 어색한 표현과 오역이 남아 있습니다.
사용자 스크린샷의 전투 HUD 인물 이름은 번역 완료를 확인하지 못했습니다.
선택지 배치, 긴 문장 줄바꿈, 모든 분기·상점·엔딩의 플레이 검증이 필요합니다.
08의 실제 실행 검사 항목과 한계는 runtime08_report.json에 기록했습니다. 모든 분기의 진행 검증을 의미하지 않습니다.
screens_before는 사용자가 남긴 이전 버전 화면이며, 08 적용 후 화면이 아닙니다.

## 검증
모든 빌드 대상의 압축·복원 검사 통과. 지도 이벤트 코드, 청크 오프셋,
첫 SLZ 압축 영역과 연결 위치, 음성 ID와 제어 코드를 보존했습니다.
지도 폰트는 4바이트 정렬, 영상 끝은 유효한 MPEG 패딩을 유지합니다.
패치 범위 밖 데이터는 Story06과 동일하며 xdelta 복원 결과의 SHA-256이 ISO와 일치합니다.

ISO: Star Ocean - First Departure (Korean Full Draft 08).iso
SHA-256: {v['sha256']}

## xdelta 적용
대상은 수정되지 않은 일본판 ISO입니다.
원본 SHA-256: 5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc
xdelta UI의 Patch에 SO1_Korean_Full_Draft_08.xdelta, Source File에 원본 일본판,
Output File에 새로운 ISO 이름을 지정합니다. 이전 한글판에 덧씌우지 마세요.
압축 파일에는 게임 전체 ISO를 포함하지 않습니다.
'''
(P/'README.md').write_text(readme,encoding='utf8')
files=['README.md','SO1_Korean_Full_Draft_08.xdelta','validation.json','coverage.json','screenshot_requirements.json','color_review_report.json','message_translations.json','tagged_build_report.json','runtime08_report.json','field_build_report.json','description_build_report.json','menu_build_report.json','table_build_report.json','segment_catalog.json','reviewed_translations.json','translation_review.json']
files += [str(f.relative_to(P)) for f in sorted((P/'hand_translations').glob('*.tsv'))]
files += [str(f.relative_to(P)) for f in sorted(screens.glob('*.jpg'))]
files += [f.name for f in sorted(P.glob('runtime08_*.png'))]
files += ['CONTEXT_TRANSLATION_08.md','compact_system_translations.json','font_order_overrides.json','font_packing.py','codec.py','tagged_dialogue.py','check_tagged_dialogue.py','layout.py','build_fields.py','font_bank.py','build_tables.py']
z=P/'SO1_Korean_Full_Draft_08_Patch.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
 for name in files:out.write(P/name,name)
with zipfile.ZipFile(z) as out:assert out.testzip() is None
print(z,z.stat().st_size,flush=True)
