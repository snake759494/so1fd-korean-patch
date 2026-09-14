from translate_local import *
def paragraphs():
 out={}
 if (P/'field_needed_segments.json').exists():field=[{'jp':s} for s in json.loads((P/'field_needed_segments.json').read_text(encoding='utf8'))]
 else:field=json.loads((P/'field_readable.json').read_text(encoding='utf8'))
 for x in field+json.loads((P/'extras_source.json').read_text(encoding='utf8')):
  for s in re.split(r'\{(?!8080)[0-9a-f]+\}',x['jp']):
   s=norm(s.replace('{8080}',''))
   if s and re.search(r'[\u3040-\u30ff\u3400-\u9fff]',s):out[s]=None
 return list(out)
if __name__=='__main__':
 import translate_local as t
 t.segments=paragraphs
 t.main()
