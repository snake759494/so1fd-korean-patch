import subprocess,imageio_ffmpeg
from movie_cues import CUES
from pathlib import Path
from PIL import Image,ImageDraw
p=Path(__file__).parent/'movies';canvas=Image.new('RGB',(480,292*4));d=ImageDraw.Draw(canvas)
for i,(name,cues) in enumerate(list(CUES.items())[1:]):
 a,b,s=max(cues,key=lambda x:len(x[2]));dest=p/(name+'_qa.png')
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-i',str(p/(name+'_korean.pmf')),'-ss',str((a+b)/2),'-frames:v','1',str(dest)],check=True)
 canvas.paste(Image.open(dest),(0,i*292+20));d.text((0,i*292),name,fill='white')
canvas.save(p/'qa_contact.png')
