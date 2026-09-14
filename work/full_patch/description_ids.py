import description_labels as dl
from build_fields import fe,labels
labels.update(dl.load())
if (dl.P/'label_corrections.json').exists():labels.update({int(k):v for k,v in dl.json.loads((dl.P/'label_corrections.json').read_text(encoding='utf8')).items()})
inv={x[1:]:i for i,x in enumerate(fe.extract.g['glyphs'])};extra=dl.mapping()
additional=dl.P/'description_additional_glyphs09.json'
if additional.exists():
 for row in dl.json.loads(additional.read_text(encoding='utf8')):
  extra[bytes.fromhex(row['bitmap'])]=row['id']
  labels[row['id']]=row['char']
def font_ids(u,f):
 base=f['hdr']+8+f['count'];ids=[]
 for i in range(f['count']):
  raw=u[base+i*24:base+(i+1)*24]
  k=inv.get(raw[:23],extra.get(raw,-1));assert k!=-1,(base,i,raw.hex())
  ids.append(k)
 return ids
