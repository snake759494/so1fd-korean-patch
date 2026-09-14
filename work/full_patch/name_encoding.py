"""Canonical names supplied by the user and a shared single-byte display alphabet."""
NAMES=[
 ('ﾗﾃｨｸｽ','라티크스','라티크스 파렌스'),
 ('ﾐﾘｰ','밀리','밀리 킬리트'),
 ('ﾄﾞｰﾝ','돈','돈 마르토'),
 ('ﾛﾆｷｽ','로닉스','로닉스 J. 케니'),
 ('ｼｳｽ','시우스','시우스 워렌'),
 ('ｲﾘｱ','이리아','이리아 실베스트리'),
 ('ﾖｼｭｱ','요슈아','요슈아 제란드'),
 ('ﾌｨｱ','피아','피아 멜'),
 ('ﾏｰｳﾞｪﾙ','마벨','마벨 프로즌'),
 ('ｱｼｭﾚｲ','아슈레이','아슈레이 반벨트'),
 ('ﾃｨﾆｰｸ','티니크','티니크 알카나'),
 ('ﾍﾟﾘｼｰ','페리시','페리시'),
 ('ｳｪﾙﾁ','웰치','웰치 빈야드'),
 ('ｴﾘｽ','에리스','에리스 제란드'),
]
SYLLABLES=''.join(dict.fromkeys(''.join(short for jp,short,full in NAMES)))
assert len(SYLLABLES)==24
ALIASES={chr(97+i):ch for i,ch in enumerate(SYLLABLES)}
ENCODING={ch:alias for alias,ch in ALIASES.items()}
FIELD_SLOTS={ch:208+i for i,ch in enumerate(SYLLABLES)}
def encode(name):return ''.join(ENCODING[c] for c in name).encode('ascii')
def defaults():return [(jp.encode('cp932'),encode(short)) for jp,short,full in NAMES]
