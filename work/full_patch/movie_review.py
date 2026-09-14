from pathlib import Path
import subprocess,json
import imageio_ffmpeg
from PIL import Image,ImageDraw
P=Path(__file__).parent;MOV=P.parents[1]/'work/extract/PSP_GAME/USRDIR/movie'
def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();dst=P/'movie_review';dst.mkdir(exist_ok=True)
 for path in MOV.glob('*_c.pmf'):
  if int(path.name[:2])<13:continue
  folder=dst/path.stem;folder.mkdir(exist_ok=True)
  subprocess.run([ff,'-v','error','-y','-i',str(path),'-an','-vf','fps=1,crop=480:92:0:180',str(folder/'%03d.png')],check=True)
  fs=sorted(folder.glob('*.png'))
  for page in range((len(fs)+35)//36):
   sheet=Image.new('RGB',(1440,12*114),'#303030');dr=ImageDraw.Draw(sheet)
   for i,f in enumerate(fs[page*36:page*36+36]):
    x=i%3*480;y=i//3*114;sheet.paste(Image.open(f),(x,y+20));dr.text((x+8,y+3),f'{int(f.stem)-1}s',fill='white')
   sheet.save(dst/f'{path.stem}_{page}.png')
  print(path.stem,len(fs),flush=True)
if __name__=='__main__':main()
