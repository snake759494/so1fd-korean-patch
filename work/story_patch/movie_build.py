from pathlib import Path
import sys,struct,re,json,subprocess,hashlib,shutil
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
MOV=ROOT/'work/extract/PSP_GAME/USRDIR/movie'
CUES={
'11_prologue_c':[
(3.8,5.2,'이세를 확인했습니다.'),(5.2,8.8,'12시 03분에 고밀도 우주 영역을 벗어납니다.'),
(9,12.2,'좋아. 좌표를 T5031로 맞춰라.'),(12.8,14,'알겠습니다.'),(14,16,'이세를 화면에 띄우겠습니다.'),
(19,21.8,'중력 좌표에서 이상 현상 확인!'),(21.8,24.9,'거대한 에너지가 비정상적인 속도로 접근 중!'),
(25,27.8,'질량은 70의 9제곱 메가톤!'),(27.8,30,'16포인트 선회! 측면 로켓 분사!'),
(32,33.4,'이 우주 영역을 이탈한다.'),(33.8,35.9,'워프 좌표 계산 개시!'),(38,41,'3, 2, 1…'),
(47,48.1,'온다!'),(48.1,51,'충격에 대비하라! 방어 실드 전개!'),
(61,64,'우주력 346년'),(64,69,'지금, 알 수 없는 힘에 의해\n새로운 시대가 시작되려 하고 있었다.'),
(70,72,'그것은 신의 뜻인가.'),(72,74,'아니면 운명의 장난인가.'),
(74,78,'그래도 인류는 아무도 밟지 않은 땅으로 나아간다.'),
(78,82,'사람들은 말한다. 「우주는 별의 바다」라고…')],
'12_rati_mili_doom_c':[
(26,27.4,'한가하네…'),(28,30.2,'한가하다는 건 평화롭다는 뜻이니까.'),
(32,34.8,'너, 밀리를 어떻게 생각하냐?'),(35,37,'응? 어떻게라니?'),
(38,40,'친구로서 충고하는데,'),(40,44,'걔는 덜렁대고,\n게다가 눈치도 없고…'),(44.8,46,'잔소리도 심하고…'),
(51,52.1,'밀리!!'),(54,57.3,'아, 아니… 그게 아니라… 이건,\n그러니까… 아하하하…'),
(58,59,'정말!'),(59,62,'그런 소리 할 틈 있으면 일해, 일!'),
(63,65,'하, 할 일이 없다고!'),(66,68,'순찰이라도 다녀오면 되잖아.'),
(68,70,'자, 나도 같이 가 줄 테니까.'),(70,71,'뭐?!'),(71,72.8,'어쩔 수 없지…'),
(73,74,'라티도 오는 거야!'),(75,78,'자! 순찰하러 가자!')]
}
def stamp(t):
 h=int(t//3600);m=int(t//60)%60;s=t%60
 return f'{h}:{m:02}:{s:05.2f}'
def pts(n):
 return bytes([0x21|((n>>29)&14),(n>>22)&255,((n>>14)&254)|1,(n>>7)&255,((n<<1)&254)|1])
def unpts(b):return ((b[0]&14)<<29)|(b[1]<<22)|((b[2]&254)<<14)|(b[3]<<7)|(b[4]>>1)
def packhead(scr):
 bits='01'+f'{scr>>30&7:03b}'+'1'+f'{scr>>15&32767:015b}'+'1'+f'{scr&32767:015b}'+'1'+'000000000'+'1'+f'{50000:022b}'+'11'+'11111'+'000'
 assert len(bits)==80
 return b'\0\0\1\xba'+int(bits,2).to_bytes(10,'big')
def pes_packets(d):
 pos=struct.unpack_from('>I',d,8)[0]
 while pos+6<=len(d):
  assert d[pos:pos+3]==b'\0\0\1',(pos,d[pos:pos+12].hex())
  ident=d[pos+3]
  if ident==0xba:n=14+(d[pos+13]&7)
  elif ident==0xb9:break
  else:n=6+int.from_bytes(d[pos+4:pos+6],'big')
  yield ident,d[pos:pos+n]
  pos+=n
def sector(pes,scr):
 body=packhead(max(0,scr))+pes
 pad=2048-len(body)
 assert pad==0 or pad>=6,(len(body),pad)
 if pad:body+=b'\0\0\1\xbe'+struct.pack('>H',pad-6)+b'\xff'*(pad-6)
 assert len(body)==2048
 return body
def build(name,src=None):
 src=src or ('02_prologue' if name.startswith('11') else '03_rati_mili_doom')
 ass='[Script Info]\nScriptType: v4.00+\nPlayResX: 480\nPlayResY: 272\nWrapStyle: 0\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,NanumSquare Neo,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1.2,0.4,2,12,12,12,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
 for a,b,s in CUES[name]:ass+=f'Dialogue: 0,{stamp(a)},{stamp(b)},Default,,0,0,0,,'+s.replace('\n','\\N')+'\n'
 (OUT/f'{name}.ass').write_text(ass,encoding='utf-8-sig')
 ff=imageio_ffmpeg.get_ffmpeg_exe();h264=OUT/f'{name}.h264'
 fonts=OUT/'movie_fonts';fonts.mkdir(exist_ok=True)
 for f in ROOT.glob('*.ttf'):shutil.copyfile(f,fonts/f.name)
 if True:
  cmd=[ff,'-v','warning','-y','-i',str(MOV/f'{src}.pmf'),'-map','0:v:0','-vf',f'ass={name}.ass:fontsdir=movie_fonts','-an','-c:v','libx264','-preset','slow','-profile:v','main','-level:v','3.0','-pix_fmt','yuv420p','-b:v','600k','-maxrate','900k','-bufsize','900k','-x264-params','aud=1:bframes=0:keyint=60:scenecut=0:ref=2','-f','h264',str(h264)]
  with (OUT/f'{name}_encode.log').open('w') as log:subprocess.run(cmd,cwd=OUT,stdout=log,stderr=log,check=True)
 raw=h264.read_bytes();starts=[m.start() for m in re.finditer(b'\x00\x00\x00\x01\x09',raw)];assert starts[0]==0
 starts.append(len(raw));aus=[raw[a:b] for a,b in zip(starts,starts[1:])]
 orig=(MOV/f'{name}.pmf').read_bytes();audio=[];allold=[];last=90000;system=None
 for ident,b in pes_packets(orig):
  if ident==0xbb and system is None:system=b
  if ident==0xbd:
   if b[7]&128:last=unpts(b[9:14])
   audio.append((last,b));allold.append(b)
 events=[(t,0,b) for t,b in audio]
 events.extend((90000+i*3003,1,b) for i,b in enumerate(aus));events.sort(key=lambda x:(x[0],x[1]))
 body=bytearray();audio_after=[];pending=bytearray()
 def flush():
  nonlocal pending
  if not pending:return
  pad=2048-len(pending)
  assert pad==0 or pad>=6
  if pad:pending+=b'\0\0\1\xbe'+struct.pack('>H',pad-6)+b'\xff'*(pad-6)
  body.extend(pending);pending=bytearray()
 def ensure(t):
  nonlocal pending
  if not pending:pending=bytearray(packhead(max(0,t-45000)))
 for t,kind,b in events:
  if kind==0:
   ensure(t)
   if len(pending)+len(b)>2048 or 0<2048-len(pending)-len(b)<6:flush();ensure(t)
   pending.extend(b);audio_after.append(b);continue
  first=True
  while b:
   extra=pts(t) if first else b'';header=b'\x80'+bytes([128 if first else 0,len(extra)])+extra
   ensure(t)
   cap=2048-len(pending)-6-len(header)
   if cap<64:flush();ensure(t);cap=2048-len(pending)-6-len(header)
   take=min(cap,len(b))
   if 0<cap-take<6:take-=6-(cap-take)
   chunk=b[:take];b=b[take:]
   pes=b'\0\0\1\xe0'+struct.pack('>H',len(header)+len(chunk))+header+chunk
   pending.extend(pes);first=False
 flush()
 assert audio_after==allold
 used=2048+len(body)
 assert used<=len(orig),(used,len(orig))
 # The game streams the ISO file's full length. Zero tail bytes leave the
 # emulator's demux queue nonempty at EOF; fill its allocated sectors with
 # valid MPEG padding packets and retain the retail stream length instead.
 while len(body)+2048<len(orig):body+=sector(b'',events[-1][0])
 header=bytearray(orig[:2048]);struct.pack_into('>I',header,12,len(body))
 result=bytes(header+body);assert len(result)==len(orig)
 (OUT/f'{name}_korean.pmf').write_bytes(result)
 report={'name':name,'frames':len(aus),'subtitles':len(CUES[name]),'audio_packets_unchanged':len(audio),'video_bytes':len(raw),'used':used,'slot':len(orig),'tail_padding':'valid MPEG sectors','sha256':hashlib.sha256(result).hexdigest()}
 (OUT/f'{name}_report.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
if __name__=='__main__':
 for name in sys.argv[1:] or CUES:build(name)
