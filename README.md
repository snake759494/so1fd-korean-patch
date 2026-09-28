# 스타 오션 First Departure PSP 한글패치

> **PSP-3000 실행 실패 보고 (#1):** 실기 로더 호환성 개선 후보 [Review 11 RC1](https://github.com/snake759494/so1fd-korean-patch/releases/tag/v0.11-rc1)을 시험판으로 제공합니다. 실기 성공은 아직 확인되지 않았으며 정식 최신판은 Review 10입니다. [조사·변경 내용](docs/ISSUE_1_PSP_LOADER.md)을 확인하세요. 아래 Review 10 전용 자동 적용 도구와 결과 해시는 RC1에 사용하지 마세요. RC1은 해당 릴리즈의 해시와 일반 xdelta 적용 방법을 사용합니다.

일본판 PSP **STAR OCEAN First Departure (ULJM05290)**용 비공식 한국어 패치입니다. 현재 배포판은 **Korean Review 10**입니다. 대사, 메뉴, 아이템 설명, 캐릭터 기본 이름과 영상 자막을 한국어로 표시하도록 번역 데이터와 글꼴, 일부 실행 코드를 수정했습니다.

[최신 xdelta 다운로드](https://github.com/snake759494/so1fd-korean-patch/releases/latest) · [작업 및 기술 설명](docs/TECHNICAL.md) · [개발 소스 안내](docs/BUILD.md) · [변경 기록](CHANGELOG.md)

릴리즈에 직접 첨부하는 파일은 **SO1_Korean_Review_10.xdelta 하나**입니다. 저장소에는 제작 소스, 자체 도구, 번역 및 검수 자료를 공개합니다. 원본·패치 적용 ISO, 추출 게임 바이너리, 영상·음성, 게임 글꼴 덤프, 세이브 스테이트는 배포하지 않습니다. GitHub가 자동 생성하는 Source code ZIP/TAR는 저장소 소스의 압축본이며 게임 파일이 아닙니다.

## 게임 소개 및 대상 버전

스타 오션은 SF와 판타지가 결합된 RPG입니다. 라티크스와 동료들이 고향을 위협하는 전염병을 계기로 우주와 시간을 넘나드는 사건에 휘말리는 이야기를 다룹니다. First Departure는 1996년 작품을 바탕으로 제작한 PSP 리메이크로, 일본에서는 2007년 12월 27일 발매되었습니다. [스퀘어 에닉스 공식 작품 소개](https://www.jp.square-enix.com/game/detail/so1/), [공식 발매 공지](https://blog.square-enix.com/eternalsphere/2007/12/first_departure.html), [시리즈 공식 개요](https://www.jp.square-enix.com/so1_fdr/overview/index.html).

이 패치는 **PSP 일본판**에만 적용합니다. 슈퍼패미컴판, 영문 PSP판, PS4/Switch의 First Departure R용 패치가 아닙니다. 파일 이름보다 아래 크기와 해시가 일치하는지가 중요합니다.

## 적용할 원본

| 항목 | 값 |
| --- | --- |
| 게임 ID | ULJM05290 |
| 원본 형식 | 수정되지 않은 일본판 ISO |
| 원본 크기 | 1,162,182,656 바이트 |
| **원본 MD5** | `a7b86fa9e5dfa394488e373e4872beb4` |
| 원본 SHA-256 | `5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc` |
| xdelta 파일 크기 | 50,426,566 바이트 |
| xdelta SHA-256 | `16421bc59e978fa1bcf7dee25bfacd99f0edce34035981f55cba95a5e456ba12` |
| 적용 결과 ISO 크기 | 1,162,182,656 바이트 |
| 적용 결과 ISO SHA-256 | `3dc5acf84ce56927199d2e9c14ead14aaed89305e88486febb96154766c9dbf7` |

이 값들은 이번 배포에 사용하는 로컬 파일을 직접 해시한 값입니다. 원본 게임 파일은 사용자가 별도로 준비해야 합니다. 이전 한글판에 덧씌우지 말고 항상 위 원본에 적용하세요.

## 패치 적용 방법

### Windows에서 원본 확인

PowerShell에서 실제 파일 경로를 넣어 실행합니다.

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath '.\Star Ocean - First Departure (Japan).iso'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Star Ocean - First Departure (Japan).iso'
```

위 표와 다르면 적용을 중단하고 원본 버전 및 파일 상태를 확인하세요. CSO 파일을 ISO처럼 이름만 바꿔서는 사용할 수 없습니다.

### xdelta UI 사용

1. 릴리즈에서 `SO1_Korean_Review_10.xdelta`를 받습니다.
2. xdelta3 패치를 지원하는 도구의 **Apply Patch** 기능을 엽니다.
3. **Patch**에 xdelta 파일, **Source File**에 해시가 일치하는 원본 ISO를 선택합니다.
4. **Output File**에 원본과 다른 새 파일명, 예를 들어 `Star Ocean - First Departure (Korean Review 10).iso`를 지정합니다.
5. 적용 완료 후 결과 ISO의 SHA-256을 위 표와 비교합니다.

UI 명칭은 도구마다 조금 다릅니다. 외부 도구 실행 파일은 이 릴리즈에 포함하지 않습니다. xdelta 자체의 소스와 배포 안내는 [공식 프로젝트](https://github.com/jmacd/xdelta)를 참고하세요.

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s '.\Star Ocean - First Departure (Japan).iso' '.\SO1_Korean_Review_10.xdelta' '.\Star Ocean - First Departure (Korean Review 10).iso'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Star Ocean - First Departure (Korean Review 10).iso'
```

원본·패치·결과의 해시를 자동 검사하는 자체 도구도 제공합니다. Python 3와 xdelta3 실행 파일을 준비한 뒤 저장소 루트에서 다음처럼 사용합니다.

```powershell
python tools/apply_release.py --xdelta '.\xdelta3.exe' --source '.\Star Ocean - First Departure (Japan).iso' --patch '.\SO1_Korean_Review_10.xdelta' --output '.\Star Ocean - First Departure (Korean Review 10).iso'
```

이 도구는 기존 출력 파일을 덮어쓰지 않습니다. 패치 적용 실패나 결과 해시 불일치 시 성공으로 처리하지 않습니다.

### PPSSPP에서 실행

게임을 완전히 종료한 뒤 새 ISO를 여세요. 이전 버전의 상태 저장(에뮬레이터 Save State)은 과거 실행 코드와 글꼴을 메모리에 보관할 수 있으므로 **게임 내 일반 저장 데이터**로 이어 하세요. 새 게임의 기본 이름은 한글로 설정됩니다. 사용자가 직접 입력한 이름을 일괄 변경하는 패치는 아닙니다.

## 작업 내용과 범위

검수 및 빌드 보고서에 집계된 작업량입니다. 중복을 제외한 번역 수와 실제 삽입 행 수는 서로 다릅니다.

| 구분 | 작업량 및 내용 |
| --- | --- |
| 전체 대사 | 고유 메시지 8,730개, 필드 뱅크 974개 |
| 색상·강조 대사 | 2,113개 검수, 색상·이름·아이템 변수 등 제어 코드 보존 |
| 메뉴·공통 문자열 | 고유 문자열 2,484개, 메뉴 뱅크 16개와 공통표 3개 |
| 설명 | 고유 설명 1,175개, 실제 설명 행 1,589개 |
| 아이템 제목 이미지 | 1,589개 검사, 1,399개 교체; 숫자·ASCII 등 190개 유지 |
| 캐릭터 이름 | 기본 이름 14명; 이름 입력·메뉴·전투·공통 메시지 글꼴 수정 |
| 영상 | 영상 7개에 자막 큐 93개; 음성은 일본어 유지 |

원문 해독과 번역 초안, 문맥·용어 검수 자료 및 최종 덮어쓰기 사전을 함께 공개합니다. 이전 초안에는 최종판과 다른 표기가 남아 있습니다. 수정할 때는 [번역 파일 우선순위](docs/BUILD.md)를 확인하세요.

주요 이름은 라티크스 파렌스, 밀리 킬리트, 돈 마르토, 로닉스 J. 케니, 이리아 실베스트리 등의 사용자 지정 표기를 반영했습니다. 화면 공간에 따라 성을 생략한 이름을 사용합니다. 전체 기준은 [등장인물 문서](docs/CHARACTER_REFERENCE.md)에 정리되어 있습니다.

## Review 10 수정 및 검증

전투 후 레벨업 문장에서 이름이 일본어 한자로 보이던 문제를 수정했습니다. 동적 이름 코드가 공통 글꼴의 일본어 칸을 가리키는 것이 원인이었습니다. 공통 글꼴 3개에 이름용 241~264번 칸을 예약하고 기존 정적 문자열의 글자 참조를 재배치했습니다.

- 원본에 xdelta를 적용한 결과와 배포용 완성 ISO의 바이트 일치 확인.
- 필드 974개 구조 검사, 메뉴·공통표 8,713행의 글꼴 및 제어 코드 대조 통과.
- 14명 × 공통 글꼴 3개 = 42개 이름 렌더링 조합 검사 통과.
- PPSSPP 1.17.1에서 라티크스·밀리·돈의 실제 레벨업 이름, 주문 습득 메시지와 전투 후 필드 복귀 확인.
- Review 09에서 새 게임 시작, 기본 이름, 오프닝, 초반 마을 및 전투 HUD를 확인. 마을 왼쪽 위 집과 상점의 멈춤 문제는 압축 블록 배치를 보존하도록 수정하고 출입을 재검증.

Review 10 레벨업 시험은 이전 시험용 상태를 불러온 뒤 새 전투 자원을 로드하여 수행했습니다. 변경된 문구·글꼴 전체가 새 ISO와 일치함을 메모리에서 확인했고 메모리 쓰기 없이 진행했습니다. 이 시험 상태에는 구버전 HUD 코드가 남아 있어 상단 이름이 영문으로 보일 수 있었습니다. Review 10 실행 파일은 새 게임 한글 HUD를 확인한 최종 Review 09와 동일합니다. 자세한 시험 조건은 [검증 보고서](validation/review10/runtime10_report.json)를 참고하세요.

**전체 루트·동료 조합·엔딩을 완주한 검증은 아닙니다. 실제 PSP 기기는 시험하지 않았습니다.** 일부 공통 획득 문장의 `은(는)`, `을(를)` 표기가 남아 있으며, 직접 입력하는 이름 화면의 일본어/영문 입력 기능은 유지됩니다. 보고서의 번역 범위 수치는 모든 상황의 무오류를 보증하는 수치가 아닙니다.

오류 제보에는 패치 버전, 결과 ISO SHA-256, PPSSPP 버전, 장소·대사·재현 순서를 적어 주세요. 기존 상태 저장으로 재현했는지도 알려 주시면 원인 구분에 도움이 됩니다. 게임 ISO나 추출 바이너리는 이슈에 첨부하지 마세요.

## 저장소 구성 및 권리

- `work/tools/`: 패킹·압축·글꼴·ISO 분석용 자체 Python 도구.
- `work/story_patch/`, `work/menu_patch/`: 초기 대사·메뉴 패치 소스.
- `work/full_patch/`: 최종 빌드·이름 처리 소스, 번역 JSON, 문맥 목록, 검수 TSV.
- `tools/`: 배포 패치 적용·공개 파일 검사 도구.
- `validation/`: Review 09/10 검증 보고서. 게임·메모리 바이너리와 시험 스테이트는 제외.
- `archive/early/`: 초기 번역 사전과 글자 판독 자료.
- `docs/`, `LICENSES/`: 제작 설명, 인물 기준, 글꼴 출처 및 라이선스.

원작 게임의 권리는 각 권리자에게 있습니다. 이 프로젝트는 공식 한국어판이 아니며 스퀘어 에닉스의 공식 지원·승인을 뜻하지 않습니다. 글꼴 및 외부 도구는 각각의 라이선스를 따릅니다. [글꼴 출처](docs/FONT_CREDITS.md)와 [권리 안내](RIGHTS.md)를 참고하세요.
