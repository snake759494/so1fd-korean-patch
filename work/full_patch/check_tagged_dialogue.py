"""Regression and actual-bank checks for contextual color translations."""
import json
from pathlib import Path
from tagged_dialogue import controls, reflow, reviewed, restore_waits, control_signature

P = Path(__file__).parent

def check():
    from codec import tokens, field_tokens
    raw = bytes.fromhex('86802c01818000')
    field = list(field_tokens(raw, [0], {0:'「'}))
    assert field[0] == ('control', bytes.fromhex('86802c01'), 0x4006)
    assert [k for k,b,v in field] == ['control', 'control', 'end']
    common = list(tokens(raw, [0], {0:'「'}))
    assert common[0][1] == bytes.fromhex('86802c')
    assert common[1] == ('glyph', b'\x01', '「')
    # New font slot assignment must never alter the special-symbol selector.
    assert control_signature(bytes.fromhex('8d800e828000'),list(range(300))) != control_signature(bytes.fromhex('8d808602828000'),list(range(300)))
    # The noun stays colored and the Korean particle stays outside that color.
    old = '男「{848001}クール{848000}から来た。{8080}よろしく。{8280}'
    new = '남자「{848001}쿠르{848000}에서 왔어. 잘 부탁해.{8280}'
    result = reflow(old, new)
    assert '{848001}쿠르{848000}에서' in result
    assert result.count('{8080}') == 1
    assert controls(old) == controls(result)
    # A lost reset, changed variable, or changed wait parameter must fail closed.
    for source, target in [
        (old, new.replace('{848000}', '')),
        ('{8c8001}「あ。{8280}', '{8c8000}「아.{8280}'),
        ('あ{868078}{8180}い{8280}', '아{868077}{8180}이{8280}'),
    ]:
        try:
            reflow(source, target)
        except ValueError:
            pass
        else:
            raise AssertionError('corrupted control accepted')
    catalog = json.loads((P / 'context_review_catalog.json').read_text(encoding='utf8'))
    translations = json.loads((P / 'message_translations.json').read_text(encoding='utf8'))
    for row in catalog:
        if str(row['id']) in translations:
            try:
                result = reflow(row['jp'], restore_waits(row['jp'], translations[str(row['id'])]))
            except ValueError as error:
                raise ValueError((row['id'], str(error))) from error
            assert controls(row['jp']) == controls(result), row['id']
            assert row['jp'].count('{8080}') == result.count('{8080}'), row['id']
    print('Regression PASS:', len(translations), 'whole messages', flush=True)

def build():
    import build_fields as b
    cache = b.load_cache()
    members = sorted({m for m, i in reviewed()})
    good, bad = [], []
    for member in members:
        try:
            good.append(b.make(member, cache))
            print(member, 'PASS', flush=True)
        except Exception as e:
            bad.append(dict(member=member, error=repr(e)))
            print(member, repr(e), flush=True)
    (P / 'tagged_build_report.json').write_text(json.dumps(
        dict(success=good, errors=bad), ensure_ascii=False, indent=2), encoding='utf8')
    if bad:
        raise SystemExit(1)

if __name__ == '__main__':
    check()
    build()
