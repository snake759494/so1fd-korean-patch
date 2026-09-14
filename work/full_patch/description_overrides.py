from pathlib import Path
import json,re
P=Path(__file__).parent
T={1808384:'유기농 오마치 쌀 특유의 깊은 맛에 개성을 더한 술. MP 회복(한 명)',6273024:'바삭한 면 위에 뜨거운 소스를 붓는 소리가 식욕을 돋운다. HP 회복(한 명)',6486016:'가 집필한 『바닥이 더럽잖니! 우리 며느리는… 하고 시어머니가 말했다』',7626752:'저에너지 반양성자 금속의 약칭'}
def overrides():
 rows=json.loads((P/'extras_source.json').read_text(encoding='utf8'))
 return {re.sub(r'\{[0-9a-f]+\}','',x['jp']):T[x['id']] for x in rows if x['kind']=='description' and x['id'] in T}
