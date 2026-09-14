from build_fields import *
def main():
 needed={}
 for bank in json.loads((P/'inventory.json').read_text(encoding='utf8'))['banks']:
  m=bank['member'];r=fe.read(m)
  for row in r['rows']:
   if (m,row['index']) in fb.T:continue
   for j,(kind,raw,s) in enumerate(parts(bytes.fromhex(row['hex']),r['ids'])):
    if kind!='text':continue
    if j==0:s=re.sub(r'^\d{5}','',s)
    if JP.search(s):needed[norm(s)]=None
  if m%100==0:print(m,len(needed),flush=True)
 (P/'field_needed_segments.json').write_text(json.dumps(list(needed),ensure_ascii=False,indent=1),encoding='utf8')
 from translate_paragraphs import paragraphs
 catalog=json.loads((P/'segment_catalog.json').read_text(encoding='utf8'));seen={x['jp'] for x in catalog}
 for s in paragraphs():
  if s not in seen:catalog.append(dict(id=len(catalog),jp=s));seen.add(s)
 (P/'segment_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=1),encoding='utf8');print('field',len(needed),'catalog',len(catalog),flush=True)
if __name__=='__main__':main()
