from pathlib import Path
import subprocess,imageio_ffmpeg,sys
from PIL import Image,ImageDraw
OUT=Path(__file__).parent
for n in sys.argv[1:]:
 d=OUT/n;d.mkdir(exist_ok=True)
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','fatal','-y','-i',str(OUT.parent/f'extract/PSP_GAME/USRDIR/movie/{n}.pmf'),'-vf','fps=1,crop=480:62:0:210',str(d/'%03d.png')],check=True)
 files=sorted(d.glob('*.png'))
 for start in range(0,len(files),24):
  im=Image.new('RGB',(520,24*65));draw=ImageDraw.Draw(im)
  for j,f in enumerate(files[start:start+24]):
   draw.text((2,j*65+20),str(start+j+.5),fill='yellow');im.paste(Image.open(f),(40,j*65))
  im.save(OUT/f'{n}_{start}.png')
