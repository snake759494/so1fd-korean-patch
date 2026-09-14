from pathlib import Path
P=Path(__file__).parent
out={}
for i,r in enumerate('HGFEDCBA'):
 out[573+i]=f'선수, {r}랭크에서 4연승을 거두었습니다! 이제 드디어 다섯 번째 상대입니다!'
 out[599+i]=f'해설자「또 한 명의 승자가 탄생했습니다! {r}랭크에서 승리한 선수는,'
for i,name in enumerate('제니퍼 메릴린 릴 샤이아 플루아 카샤 레시 메이리 첼시 뮤키 마나 마크 멜 류 케니 크레스 유마 류야 존 스트레이야 루시오'.split()):
 title='프린세스' if i<11 else '프린스'
 out[616+i]=f'해설자「승자에게 꽃다발을 증정할 로열 {title}는 {name} 씨입니다!'
(P/'hand_translations/0500_templates.tsv').write_text('\n'.join(f'{k}\t{v}' for k,v in sorted(out.items()))+'\n',encoding='utf8')
