"""The 272-glyph prefix every Star Ocean 1 text bank starts with."""

KANA = (
    "「、。を"
    "ぁぃぅぇぉゃゅょっゎ"
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん"
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
    "ヲ"
    "ァィゥェォャュョッー"
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン"
    "ヴ"
    "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ"
    "ヵヶヮ"
    "0123456789"
    "-."
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
)

# 233.. : the paired entries are halfwidth / fullwidth variants of the same mark;
# slot 253 is the full-width blank
SYMBOLS = "･・?？!！)）]］>＞♪(（[［<＜『　=:;、,/"

KANJI = "読開装備自動的変更×手入所"

PREFIX = KANA + SYMBOLS + KANJI

assert len(KANA) == 233, len(KANA)
assert len(SYMBOLS) == 27, len(SYMBOLS)
assert len(PREFIX) == 273, len(PREFIX)

# a Korean-safe rendering of the marks that have no direct equivalent
TRANSLIT = {"･": "·", "・": "·", "『": "「"}


def char(index: int) -> str | None:
    return PREFIX[index] if 0 <= index < len(PREFIX) else None


if __name__ == "__main__":
    for i in range(0, 272, 16):
        print(f"{i:3d}: {PREFIX[i:i + 16]}")
