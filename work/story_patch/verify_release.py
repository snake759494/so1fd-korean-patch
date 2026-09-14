from pathlib import Path
import json,hashlib
P=Path(__file__).parent
r=json.loads((P/'iso_report.json').read_text())
with open(r['target'],'rb') as f:
 for x in r['changes']:
  f.seek(x['offset'])
  data=Path(x['file']).read_bytes()
  assert f.read(x['size'])==data,x['file']
  assert hashlib.sha256(data).hexdigest()==x['sha256']
v=json.loads((P/'validation.json').read_text())
h=hashlib.sha256()
with open(r['target'],'rb') as f:
 for data in iter(lambda:f.read(4*1024*1024),b''):h.update(data)
assert h.hexdigest()==v['patched_sha256']
reports=[json.loads(p.read_text(encoding='utf8')) for p in sorted(P.glob('*_report.json')) if p.stem.split('_')[0].isdigit()]
reports=[x for x in reports if 'strings' in x]
coverage={'map_banks':len(reports),'translated_strings':sum(len(x['strings']) for x in reports),'movie_subtitles':38,'runtime_checked':['Both Korean subtitled movies and automatic transitions','First field loading','Cratos movement and resident dialogue','Dorn patrol dialogue with portrait'],'runtime_not_fully_checked':['All translated event branches','Bandit battle and subsequent progression through Kool'],'tested_iso_sha256':h.hexdigest()}
coverage['version']='06'
coverage['runtime_checked']+=['Raty house entry, Korean mother dialogue and exit','Weapon shop entry and exit','Tool shop entry, movement and exit','Food shop entry and exit','Consecutive indoor/outdoor transitions after preserving original SLZ first-block allocation/link']
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(coverage,ensure_ascii=False,indent=2))
