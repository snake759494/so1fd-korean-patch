from pathlib import Path
import json
P=Path(__file__).parent
PAGES=[
'''物作食性中器武具
整身生議敵攻大強
紙薬出風肉無感水
気形長／効子見消
道書酒能確貴辞名
銀受放護意向%了
○足●盾知海振□
□色美移，扱空部''',
'''重極破流靴牛善王
下示英雄尋面車5
換内要残可魂元事
現在基格夢程異頭
宿勇両士容瓜当業
片囲治離起画認判
除易始信流塊コォ
家興私素究装接ィ''',
'''息惑置駆求宇宙驚
霧餃噌鞭鍋睡&衿
指験老紅統池悩周
官骨関折考干透炸
凍L♪67e店ふ
町夜住点図潜環境
校常習豊卒節疾+
−親同河♀篇蝋棺''',
'''膏媚燕碗梨粉粕京
巾倍醸餅仔喰αβ
γ沁鷹淒擬壷鳳甕
茹鮭灼酢挽社揚笹
汁喝爆←口紙0×
CDR89.ar
cn○特警舌雲台
教段妃研枚蔵推奨''',
'''位脱包従慣積戻永
射銃愛筋卒犬頬北
ュヲヌル足!☆★
ABFGHJLＭ
NQUVWXYZ
=:;,hdv隊
館買船視門席控左
寝閉庫路脈'''
]
def load():
 ids=json.loads((P/'extra_glyph_order.json').read_text());out={}
 for i,s in enumerate(PAGES):
  chars=''.join(s.split());ks=ids[i*64:i*64+64]
  assert len(chars)==len(ks),(i,len(chars),len(ks))
  out.update(zip(ks,chars))
 return out
