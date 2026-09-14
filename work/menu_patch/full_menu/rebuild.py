from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent
STEPS=['build.py','patch_names.py','patch_textures.py','patch_small_font.py','patch_descriptions.py','patch_name_backgrounds.py','patch_common.py','patch_psp_common.py','patch_executable.py','assemble.py','validate.py']
if __name__=='__main__':
 for step in STEPS:subprocess.run([sys.executable,str(HERE/step)],check=True,cwd=HERE.parents[2])
