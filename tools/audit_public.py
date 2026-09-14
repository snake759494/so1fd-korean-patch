"""Audit this text-only publishing tree; never scans .git contents."""
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'.py', '.json', '.tsv', '.txt', '.md'}
SECRET = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')

def main():
    errors, records = [], []
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if '.git' in rel.parts or not path.is_file():
            continue
        if path.suffix not in ALLOWED and path.name != '.gitignore':
            errors.append(f'{rel}: unexpected file type')
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeError:
            errors.append(f'{rel}: not UTF-8 text')
            continue
        if b'\0' in raw or SECRET.search(text):
            errors.append(f'{rel}: binary content or credential pattern')
        if re.search(r'[0-9a-fA-F]{1024,}', text):
            errors.append(f'{rel}: possible embedded binary hex dump')
        if path.suffix == '.json':
            json.loads(text)
        if path.suffix == '.py':
            ast.parse(text, filename=str(rel))
        if path.name != 'publication_manifest.json':
            records.append({'path': rel.as_posix(), 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
    if errors:
        raise SystemExit('\n'.join(errors))
    (ROOT/'publication_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'PASS: {len(records)} UTF-8 source/document/translation files; no forbidden file types or detected credentials.')

if __name__ == '__main__':
    main()
