"""User-approved spellings applied last to translation targets, never controls."""
REPLACEMENTS = {
 '라틱스':'라티크스', '로니키스':'로닉스', '애슐리':'아슈레이',
 '제랜드':'제란드', '아르카나':'알카나', '워런':'워렌', '키리트':'킬리트',
 '라이아스':'라이어스', '무어':'무아', '오타님':'오터님',
 '메토크스':'메토쿠스', '파지 신전':'퍼지 신전', '트로프':'트롭',
 '에크다트':'엑더트', '두르스':'둘스', '파게트':'파겟',
 '이비나':'이레나', '베이즈':'베이스', '칼나스':'카르나스',
 '진홍의 방패':'붉은 방패', '구이종족':'구 이종족',
}

def canonicalize(text):
 for old,new in REPLACEMENTS.items():text=text.replace(old,new)
 return text
