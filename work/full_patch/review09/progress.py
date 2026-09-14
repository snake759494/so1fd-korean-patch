"""Report actual reviewed coverage without treating machine drafts as reviewed."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
path=P/'message_translations.json'
t=json.loads(path.read_text(encoding='utf8'))
done=[r for r in c if str(r['id']) in t]
pending=[r['id'] for r in c if str(r['id']) not in t]
colored=[r for r in c if r.get('has_color')]
def evidence(name):
 f=P/name
 return json.loads(f.read_text(encoding='utf8')) if f.exists() else {}
validation=evidence('validation.json');runtime=evidence('review09/runtime09_report.json')
iso=Path(validation.get('iso','_missing'))
built=iso.is_file() and validation.get('delta_roundtrip')=='PASS'
if built:
 h=hashlib.sha256()
 with iso.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 built=h.hexdigest()==validation.get('sha256')
tested=built and runtime.get('release_smoke_pass',False) and runtime.get('final_iso_sha256')==validation.get('sha256')
report={
 'status':'BUILT_AND_SMOKE_TESTED' if tested else 'BUILD_OR_RUNTIME_VALIDATION_PENDING',
 'unique_messages':len(c),
 'reviewed_message_overrides':len(done),
 'unreviewed_messages':len(pending),
 'reviewed_percent':round(100*len(done)/len(c),2),
 'colored_messages':len(colored),
 'reviewed_colored_messages':sum(str(r['id']) in t for r in colored),
 'message_translations_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'pending_ids':pending,
 'review09_iso_built':built,
 'review09_runtime_tested':tested,
 'full_game_all_routes_playtested':False,
 'notes':[
  'Only explicitly authored reviews and identical-source layout variants are in the review map.',
  'Control sequence and parameters, including field u16 wait values, pass check_tagged_dialogue.check().',
  'Current structural checks do not constitute game runtime or complete translation quality validation.',
  'The existing Draft 08 release has not been overwritten.',
  'Menu, item descriptions and bitmap headings have dedicated binary validation reports.',
  'Runtime coverage is recorded by ISO hash; all routes and endings have not been playtested.'
 ]}
(P/'review09'/'progress.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('pending_ids','notes')},ensure_ascii=False,indent=1))
