from pathlib import Path
p=Path(__file__).with_name('translations.py')
s=p.read_text(encoding='utf8').replace(",'''",",r'''")
p.write_text(s,encoding='utf8')
