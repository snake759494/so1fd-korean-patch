"""Word wrapping that preserves the game's original newline count."""
import re
from functools import lru_cache
def pixels(text):return sum(6 if ord(c)<128 else 12 for c in re.sub(r'\{[0-9a-f]+\}','',text))
def wrap_dialogue(text,limit=204):
 lines=[]
 for paragraph in text.replace('\\n','\n').split('\n'):
  line='';width=0
  for word in paragraph.split(' '):
   w=12*len(re.sub(r'\{[0-9a-f]+\}','',word))
   if line and width+12+w>limit:lines.append(line);line='';width=0
   if line:line+=' ';width+=12
   # Rare unspaced long words must still fit the dialogue box.
   for token in re.findall(r'\{[0-9a-f]+\}|.',word):
    tw=0 if token.startswith('{') else 12
    if width+tw>limit:lines.append(line);line='';width=0
    line+=token;width+=tw
  lines.append(line)
 return ''.join((('{8180}' if i%3==0 else '{8080}') if i else '')+line for i,line in enumerate(lines))
@lru_cache(maxsize=32768)
def wrap_fixed(text,lines,fixed_cells=False):
 assert lines>=1
 # A choice marker must stay with its own option, not the preceding option.
 choices=re.split(r'(?=[·･])',text)
 choices=[x.strip() for x in choices if x.strip()]
 if 1<len(choices)<=lines and all(x[0] in '·･' for x in choices):
  return tuple(choices+['']*(lines-len(choices)))
 words=text.split(' ');n=len(words);used=min(n,lines)
 prefix=[0]
 for w in words:prefix.append(prefix[-1]+(12*len(re.sub(r'\{[0-9a-f]+\}','',w)) if fixed_cells else pixels(w)))
 def width(i,j):return prefix[j]-prefix[i]+(12 if fixed_cells else 6)*max(0,j-i-1)
 # First minimize the widest line, then prefer an even distribution.
 dp={(0,0):(0,0,())}
 for k in range(1,used+1):
  for j in range(k,n+1):
   best=None
   for i in range(k-1,j):
    prev=dp.get((k-1,i))
    if prev is None:continue
    w=width(i,j);candidate=(max(prev[0],w),prev[1]+w*w,prev[2]+(i,))
    if best is None or candidate[:2]<best[:2]:best=candidate
   dp[k,j]=best
 starts=dp[used,n][2]+(n,)
 out=[' '.join(words[starts[i]:starts[i+1]]) for i in range(used)]
 return tuple(out+['']*(lines-used))
