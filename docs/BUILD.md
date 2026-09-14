# 개발 및 번역 자료 안내

일반 사용자는 README의 xdelta 적용 절차만 따르면 됩니다. 이 저장소는 실제 제작에 사용한 소스와 번역 자료를 공개하는 개발 아카이브입니다. 원본에서 추출한 중간 자료와 과거 시험용 ISO를 포함하지 않으므로, clone 직후 전체 빌드 한 번으로 같은 ISO를 재생성하는 환경은 아닙니다.

## 환경과 외부 의존성

제작 환경은 Windows, Python 3.13, PPSSPP 1.17.1입니다. 주요 Python 의존성은 Pillow, numpy, websocket-client, imageio-ffmpeg이며, 역어셈블 분석에는 capstone을 사용합니다. 번역 초안 생성 스크립트의 선택적 의존성은 ctranslate2 및 transformers입니다. 확정된 번역을 사용하는 단계에서는 초안 생성 모델을 다시 실행할 필요가 없습니다. 모델 파일은 배포하지 않습니다.

xdelta3, 영상 처리 도구 및 글꼴은 별도로 준비합니다. Galmuri11 및 NanumSquareNeo Bold의 출처는 FONT_CREDITS.md에 있습니다. 자체 도구 소스만 포함하며 외부 실행 파일과 글꼴 파일은 포함하지 않습니다.

## 빌드 구조와 현재 제약

기존 스크립트의 상대 위치를 유지하기 위해 `work/` 구조를 보존했습니다. 다수 분석 도구는 원래 로컬 경로, 추출 결과, pickle 캐시와 특정 PPSSPP 디버거 포트를 참조합니다. 자신의 경로에 맞게 설정하고 코드를 읽은 뒤 필요한 단계만 실행하세요. 과거 시험 스크립트에는 실행 중인 에뮬레이터 조작 및 메모리 시험 코드가 있습니다.

제작 흐름은 다음과 같습니다.

1. 해시가 일치하는 일본판 ISO를 로컬에 준비합니다. `work/tools/iso9660.py`, `so1pack.py`, `slz.py` 및 관련 추출 도구로 패키지·압축 자료를 분석합니다.
2. 대사·메뉴의 문자 코드, 글꼴과 위치 정보를 로컬에서 추출합니다. 공개하지 않은 `field_original.json`, 원본 비트맵 목록, 추출 member 바이너리와 캐시는 이 단계의 로컬 자료입니다. 단순히 빈 JSON으로 대체하면 안 됩니다.
3. `work/full_patch/build_fields.py`, `build_menus.py`, `build_descriptions.py`, `build_tables.py`가 번역과 글꼴을 삽입합니다. `build_item_titles.py`는 설명 빌드 뒤 아이템 제목을 처리합니다. `build_name_fonts.py`, `build_battle_name_fonts.py`, `build_name_executable.py`는 이름 글꼴·실행 코드를 처리합니다. 영상은 `build_movies.py` 및 관련 영상 스크립트가 담당합니다.
4. 최종 `assemble10.py`는 로컬의 **Korean Story 06 ISO**를 기준으로 생성된 member·영상·실행 파일을 합칩니다. 따라서 원본뿐 아니라 앞선 제작 단계의 결과도 필요합니다. 이 중간 ISO는 저장소나 릴리즈에 포함하지 않습니다.
5. `validate10.py`는 원본과 기준 ISO, 변경 범위, 필드 구조, xdelta 왕복 일치를 확인합니다. 실제 게임 검증은 별도로 진행해야 합니다.

이 목록은 구조 설명이며 완전 자동화된 재현 명령 목록이 아닙니다. 원본 추출부터 모든 캐시를 재생성하는 이식 작업과 경로 정리가 추가로 필요합니다. 과거 `release*.py`는 당시 내부 ZIP 패키징 코드입니다. 이번 GitHub 배포 규칙은 **릴리즈 첨부 xdelta 1개**이며, 과거 ZIP 생성 결과를 그대로 업로드하지 않습니다.

## 번역 데이터

현재 사용 데이터는 `work/full_patch/`에 있습니다.

| 파일 | 역할 |
| --- | --- |
| `message_translations.json` | 제어 코드를 포함한 전체 메시지 단위 최종 번역 |
| `translation_cache.json` | 초기 문구·세그먼트 번역 캐시 |
| `name_transliterations.json`, `reviewed_translations.json` | 이름 및 검수 덮어쓰기 |
| `terminology_review09.json` | 최종 용어 검수 |
| `menu_review09.json` | 메뉴·공통표 검수 |
| `description_review09.json`, `description_control_review09.json` | 설명 및 변수 포함 설명 검수 |
| `segment_catalog.json`, `hand_translations/*.tsv` | 세그먼트 ID와 수동 번역 연결 |
| `review09/*.tsv` | 문맥·메뉴·설명·화면 줄바꿈 검수 이력 |
| `context_review_catalog.json` | 원문, 번역, 위치 정보만 남긴 공개 문맥 목록 |
| `canonical_names.py`, `review09/apply_user_names.py` | 사용자 지정 인명 표기 반영 |

캐시만 수정하면 후속 검수 사전이 다시 덮어쓸 수 있습니다. 실제 우선순위는 `build_fields.load_cache()`와 `tagged_dialogue.py`, 각 메뉴·설명 빌드 코드가 결정합니다. 완전한 문장의 수정은 최종 메시지 사전도 함께 확인하세요. 공개 문맥 목록은 최신 전체 메시지 번역을 반영했으며 바이너리 덤프용 파일이 아닙니다.

중괄호 안의 16진 제어 토큰은 번역 문자가 아닙니다. 색상·강조, 인물 이름, 아이템 변수, 대기·줄바꿈 등을 나타냅니다. 토큰을 지우거나 일반 문장으로 번역하면 색상뿐 아니라 메시지 흐름이 깨질 수 있습니다. 구조 검사와 실제 해당 장면 확인을 함께 수행해야 합니다.

## 공개 파일 관리

`python tools/audit_public.py`로 텍스트 허용 목록, 비밀키 패턴, 큰 바이너리 문자열을 검사합니다. 새로 추가한 파일은 직접 내용도 검토하세요. ISO·추출 자원·RAM·스테이트·영상·폰트·에뮬레이터·모델은 Git 밖에서 관리합니다. 공개 manifest는 파일 해시 목록이며 게임 데이터가 아닙니다.
