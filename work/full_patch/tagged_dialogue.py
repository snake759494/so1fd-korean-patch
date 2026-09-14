"""Reviewed whole messages: formatting codes never become translation boundaries."""
import json
import re
from pathlib import Path
from functools import lru_cache
from codec import field_tokens as tokens
from layout import wrap_fixed

P = Path(__file__).parent
TAG = re.compile(r'\{([0-9a-f]+)\}')

def controls(text):
    return [m.group(1) for m in TAG.finditer(text) if m.group(1) != '8080']

def restore_waits(source, target):
    """Restore legacy u8 catalog spelling only against the exact u16 source."""
    waits = iter(re.findall(r'\{(8680[0-9a-f]{4})\}', source))
    def restore(match):
        original = next(waits, None)
        if original is None or not original.startswith(match.group(1)):
            raise ValueError('wait parameter mismatch')
        return '{' + original + '}'
    return re.sub(r'\{(8680[0-9a-f]{2}(?:[0-9a-f]{2})?)\}', restore, target)

def reflow(source, target):
    """Keep page/wait/variable boundaries, reflow across color changes."""
    if controls(source) != controls(target):
        raise ValueError(('reviewed message control mismatch', controls(source), controls(target)))
    # A color run is part of the surrounding sentence, including its particles.
    boundary = re.compile(r'(\{(?!8480|8080)[0-9a-f]+\})')
    src = boundary.split(source)
    dst = boundary.split(target)
    if len(src) != len(dst):
        raise ValueError('message boundary mismatch')
    out = []
    for old, new in zip(src, dst):
        if boundary.fullmatch(old):
            out.append(new)
        elif '{8080}' in new:
            if old.count('{8080}') != new.count('{8080}'):
                raise ValueError('explicit newline count mismatch')
            out.append(new)
        else:
            out.append('{8080}'.join(wrap_fixed(new, old.count('{8080}') + 1, fixed_cells=True)))
    return ''.join(out)

@lru_cache(None)
def reviewed():
    path = P / 'message_translations.json'
    if not path.exists():
        return {}
    translations = json.loads(path.read_text(encoding='utf8'))
    catalog = json.loads((P / 'field_readable.json').read_text(encoding='utf8'))
    result = {}
    for row in catalog:
        value = translations.get(str(row['id']))
        if value is None:
            continue
        for member, index in row['locations']:
            result[member, index] = value
    return result

def replacement(member, index, raw, ids, labels):
    target = reviewed().get((member, index))
    if target is None:
        return None
    decoded = list(tokens(raw, ids, labels))
    # 400d's following byte selects a special symbol. The legacy catalog
    # spells that byte as a kana/punctuation glyph; never allocate it a new
    # Hangul font slot. Keep the original byte without changing the codec.
    special_symbols = []
    for pos, (kind, code, value) in enumerate(decoded):
        if kind == 'control' and value == 0x400d:
            following = decoded[pos + 1]
            if following[0] != 'glyph' or len(following[1]) != 1:
                raise ValueError(('unsupported special symbol', member, index))
            special_symbols.append((following[2], following[1]))
    symbols = iter(special_symbols)
    # The older review catalog omitted the high byte of u16 wait parameters.
    # Restore it from this exact original message; never invent a duration.
    source = ''.join(v if k == 'glyph' else '{' + b.hex() + '}'
                     for k, b, v in decoded if k != 'end')
    target = restore_waits(source, target)
    # The leading five digits select a voice clip and must retain original bytes.
    prefix = b''
    if re.match(r'^\d{5}', source):
        if re.match(r'^\d{5}', target):
            if target[:5] != source[:5]:
                raise ValueError(('voice prefix mismatch', member, index))
            target = target[5:]
        prefix, source = raw[:10], source[5:]
    target = reflow(source, target)
    result = [('raw', prefix, None)] if prefix else []
    cursor = 0
    for tag in TAG.finditer(target):
        if tag.start() > cursor:
            result.append(('ko', b'', target[cursor:tag.start()]))
        result.append(('raw', bytes.fromhex(tag.group(1)), None))
        cursor = tag.end()
        if tag.group(1) == '8d80':
            spelling, operand = next(symbols)
            if not target.startswith(spelling, cursor):
                raise ValueError(('special symbol operand changed', member, index))
            result.append(('raw', operand, None))
            cursor += len(spelling)
    if cursor < len(target):
        result.append(('ko', b'', target[cursor:]))
    endings = [b for k, b, v in decoded if k == 'end']
    if endings:
        assert raw.endswith(b''.join(endings)), (member, index, 'interior terminator')
        result.append(('raw', b''.join(endings), None))
    return result

def control_signature(raw, ids):
    """Color may cross a newline; executable controls and line counts stay fixed."""
    decoded = list(tokens(raw, ids, {}))
    special = [decoded[i+1][1] for i,(k,b,v) in enumerate(decoded)
               if k == 'control' and v == 0x400d]
    stream = [(b, v) for k, b, v in decoded if k != 'glyph']
    return ([b for b, v in stream if v != 0x4000],
            sum(v == 0x4000 for b, v in stream), special)
