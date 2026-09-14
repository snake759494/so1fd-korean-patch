from patch_textures import *
PATTERNS={
'라':['11100100','00100100','11100100','10000111','11100100','00000100','00000100','00000000'],
'티':['11100100','10000100','11100100','10000100','11100100','00000100','00000100','00000000'],
'밀':['11100100','10100100','10100100','11100100','01111100','00000100','01111100','01111100'],
'리':['11100100','00100100','11100100','10000100','11100100','00000100','00000100','00000000'],
'돈':['01111100','01000000','01111100','00010000','01111100','01000000','01000000','01111100'],
'폴':['01111100','00101000','01111100','00010000','01111100','00000100','01111100','01111100'],
'전':['11100100','01011100','10100100','00000100','01000000','01000000','01111100','00000000'],
'투':['01111100','01000000','01111100','01000000','01111100','00000000','01111100','00010000'],
'횟':['01000100','11100100','10100100','01000100','11111100','00010000','00101000','01000100'],
'수':['00010000','00101000','01000100','00000000','01111100','00010000','00010000','00000000']}
ALIAS=dict(zip('QJYZ;#$&=[','라티밀리돈폴전투횟수'))
def main():
 for m in [2326,2330,2334,2338,2342,2372]:
  path=OUT/f'member{m}_korean.bin';t=tree.parse(path.read_bytes(),str(m));leaf=tree.find(t,f'{m}!/1');im,at=tim(leaf.data);idx=Image.frombytes('L',im.size,bytes(v//17 for v in im.tobytes()))
  for a,ch in ALIAS.items():
   cell=ord(a)-32;x=cell%32*8;y=cell//32*8
   for yy,row in enumerate(PATTERNS[ch]):
    for xx,v in enumerate(row):idx.putpixel((x+xx,y+yy),15*int(v))
  vals=idx.tobytes();data=bytearray(leaf.data);data[at:at+len(vals)//2]=bytes(vals[i]|vals[i+1]<<4 for i in range(0,len(vals),2));tree.mark(t,leaf.path,bytes(data));path.write_bytes(tree.build(t))
  if m==2330:idx.point(lambda v:v*17).resize((1024,192),Image.Resampling.NEAREST).save(OUT/'small_atlas_korean.png')
 print('small name and counter font built')
if __name__=='__main__':main()
