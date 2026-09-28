# Korean Review 11 RC1 — PSP 실기 실행 호환성 수정 후보

[이슈 #1](https://github.com/snake759494/so1fd-korean-patch/issues/1)의 PSP-3000 구동 실패를 조사하여, 실기 CFW 로더가 사용하는 ELF 섹션·모듈 정보를 복원했습니다. 프로그램 헤더도 파일 앞부분으로 옮겼습니다. **실기 구동 성공은 아직 확인되지 않은 시험판입니다.** 정식 최신판은 Review 10으로 유지합니다.

보고자의 CFW 버전과 오류 번호가 아직 없어 보고된 현상의 확정 원인이라고 단정하지 않습니다. [상세 조사 및 변경 내용](https://github.com/snake759494/so1fd-korean-patch/blob/main/docs/ISSUE_1_PSP_LOADER.md)을 확인하세요.

## 적용

첨부 파일은 `SO1_Korean_Review_11_RC1.xdelta` 하나입니다. **수정되지 않은 일본판 PSP ISO (ULJM05290)**에 적용하세요. Review 10 한글 ISO에 덧씌우지 마세요. 원본·완성 ISO는 제공하지 않습니다.

```powershell
.\xdelta3.exe -d -s '.\Star Ocean - First Departure (Japan).iso' '.\SO1_Korean_Review_11_RC1.xdelta' '.\Star Ocean - First Departure (Korean Review 11 RC1).iso'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Star Ocean - First Departure (Korean Review 11 RC1).iso'
```

xdelta UI에서는 Patch에 RC1 xdelta, Source에 원본, Output에 새 ISO 이름을 지정합니다. 저장소의 `tools/apply_release.py`는 Review 10 전용이므로 RC1에 사용하지 마세요.

| 항목 | 값 |
| --- | --- |
| 원본 MD5 | `a7b86fa9e5dfa394488e373e4872beb4` |
| 원본 SHA-256 | `5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc` |
| 원본·완성 ISO 크기 | 1,162,182,656 바이트 |
| RC1 xdelta 크기 | 50,426,819 바이트 |
| RC1 xdelta SHA-256 | `b3de706f0e6ee727749d992b355d806ba9fc1ea8e3825e2058ea51ad6c09d508` |
| RC1 완성 ISO SHA-256 | `a584ddddc23f50d3927f1a5b0c159e5a04a415a8a13acd325c965bea55d93b08` |

## 검증 결과와 한계

- 원본→xdelta 적용 결과가 RC1 완성 ISO와 SHA-256 일치.
- 원본 ELF 섹션 24개와 `.rodata.sceModuleInfo` 조회 복원 확인.
- 게임 메모리에 로드하는 코드·후크 바이트 및 주소가 Review 10과 동일함을 검사.
- BOOT/EBOOT와 디렉터리 파일 크기 외의 ISO 바이트가 Review 10과 동일함을 검사. 번역·글꼴·영상 자원은 변경하지 않음.
- PPSSPP 1.17.1에서 상태 저장 없이 새로 부팅해 시작 영상 진입 확인.
- PSP-3000 실기, 새 게임 이후 진행, 전체 루트 검증은 이번 RC1에서 수행하지 않음. 별도 타이틀 캡처 과정은 디버거 대기 때문에 완료하지 못했으며 성공 검사에 포함하지 않음.

실기 확인 후 이슈에 PSP 모델, CFW 이름·버전, 원본 실행 여부, RC1의 오류 번호 또는 실행 결과를 남겨 주세요. 게임을 완전히 종료한 뒤 새 ISO로 실행하고 이전 에뮬레이터 스테이트는 사용하지 마세요. **이슈 #1은 실기 확인 전까지 열어 둡니다.**
