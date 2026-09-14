import re
# Field scripts use a u16 duration; the common/menu renderer uses a u8 operand.
PARAM={0x4003,0x4004,0x4006,0x400c,0x400e}
PARAM_BYTES={v:1 for v in PARAM}
def tokens(data,ids,labels,wait_bytes=1):
 i=0
 while i<len(data):
  a=i;v=data[i];i+=1
  if v==0:
   yield ('end',data[a:i],None);continue
  if v>=128:
   if i==len(data):raise ValueError('truncated glyph')
   v=(v&127)+128*data[i];i+=1
  if v>=0x4000:
   i+=wait_bytes if v==0x4006 else PARAM_BYTES.get(v,0)
   if i>len(data):raise ValueError('truncated control parameter')
   yield ('control',data[a:i],v)
  elif v<=len(ids):yield ('glyph',data[a:i],labels.get(ids[v-1],'{g'+str(ids[v-1])+'}'))
  else:raise ValueError(('glyph outside bank',v,len(ids)))

def field_tokens(data,ids,labels):
 return tokens(data,ids,labels,wait_bytes=2)
def decode(data,ids,labels):
 return ''.join(value if kind=='glyph' else ('{'+raw.hex()+'}' if kind=='control' else '') for kind,raw,value in tokens(data,ids,labels))
