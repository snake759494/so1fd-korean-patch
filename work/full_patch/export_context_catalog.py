"""Full-message review queue, using the current decoder and stable old IDs."""
import json,re
from collections import defaultdict
from build_fields import P,fe,labels,tokens

catalog=json.loads((P/'field_readable.json').read_text(encoding='utf8'))
translations=json.loads((P/'message_translations.json').read_text(encoding='utf8'))
groups=defaultdict(list)
for row in catalog:
    member,index=row['locations'][0]
    groups[member].append((row,index))
out=[]
for member,group in groups.items():
    bank=fe.read(member)
    for row,index in group:
        raw=bytes.fromhex(bank['rows'][index]['hex'])
        source=''.join(v if k=='glyph' else '{'+b.hex()+'}'
                       for k,b,v in tokens(raw,bank['ids'],labels) if k!='end')
        source=re.sub(r'^\d{5}','',source)
        out.append(dict(id=row['id'],jp=source,ko=translations.get(str(row['id'])),
                        locations=row['locations'],has_color='{8480' in source,
                        reviewed_whole_message=str(row['id']) in translations))
out.sort(key=lambda x:x['id'])
(P/'context_review_catalog.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8')
print('Context review queue:',len(out),'messages;',sum(x['reviewed_whole_message'] for x in out),'reviewed')
