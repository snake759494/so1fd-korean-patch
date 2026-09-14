from pathlib import Path
import zipfile,json,hashlib
P=Path(__file__).parent
files=['README.md','SO1_Korean_Story_06.xdelta','validation.json','coverage.json','field_audit.json','translations.py','field_extract.py','field_build.py','movie_build.py','assemble.py','validate.py','audit_fields.py','verify_release.py','package_release.py','screens/prologue_korean.jpg','screens/intro_korean.jpg','screens/resident_dialogue.jpg','screens/house06_dialogue.jpg','screens/toolshop06.jpg','screens/foodshop06.jpg']
z=P/'SO1_Korean_Story_06_Patch.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
 for name in files:f.write(P/name,name)
with zipfile.ZipFile(z) as f:assert f.testzip() is None
manifest={'zip':z.name,'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'delta_sha256':hashlib.sha256((P/'SO1_Korean_Story_06.xdelta').read_bytes()).hexdigest(),'files':files}
(P/'release_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(z, z.stat().st_size,'ZIP integrity PASS')
