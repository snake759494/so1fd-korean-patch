from build_fields import *
from codec import tokens
from description_ids import font_ids
from collections import defaultdict,Counter
PAIRS='''指かれた=描かれた
消貴=消費
喉かな=暖かな
全負=全員
偶しく=優しく
感す=癒す
感して=癒して
呼び尋せ=呼び寄せ
幸り伝る=葬り去る
添黒=漆黒
自己懐性=自己犠牲
示知=未知
者負=背負
旅女=彼女
繋が=髪が
紙章=紋章
約ぎ=紡ぎ
その者=その背
譲く=轟く
整ち扱き=撃ち抜き
過伝=過去
的郷=故郷
お妬さん=お姉さん
繋の毛=髪の毛
指いた=描いた
攻整=攻撃
割れて=倒れて
全減=全滅
お玉=お宝
辞見=発見
捜け=授け
首色=音色
首を辞生=音を発生
鍵整=鍵盤
指理=指揮
真美=真実
堅定=鑑定
丁容=丁寧
密く=多く
素時らしい=素晴らしい
逃げる突=逃げる際
太の葉=木の葉
偶れた=優れた
純細=繊細
決特=独特
捜って=寄って
尋って=寄って
名エ=名工
金細エ=金細工
狩蒲=狩猟
値物=植物
海凍=海藻
業め=集め
野葬=野菜
感靴=感触
賞悟=覚悟
味賞=味覚
感賞=感覚
特味=特殊
転の部分=鍔の部分
考々しい=若々しい
牡蜥=牡蠣
新固=新聞
太の葉=木の葉'''
def main():
 pairs=[x.split('=') for x in PAIRS.splitlines()];votes=defaultdict(Counter);examples=defaultdict(list);orig=fe.p.read(3731)
 for row in json.loads((ROOT/'work/menu_patch/full_menu/item_descriptions.json').read_text(encoding='utf8')):
  u=fe.slz.decompress(orig[row['offset']:]);ids=font_ids(u,row['font']);ss=[];gids=[]
  for k,b,v in tokens(bytes.fromhex(row['hex']),ids,labels):
   if k=='glyph':ss.append(v);code=b[0] if len(b)==1 else(b[0]&127)+128*b[1];gids.append(ids[code-1])
   else:ss.append(' ');gids.append(None)
  if not all(len(x)==1 for x in ss):continue
  s=''.join(ss)
  for a,b in pairs:
   assert len(a)==len(b),(a,b)
   for match in re.finditer(re.escape(a),s):
    for j,(ac,bc) in enumerate(zip(a,b)):
     if ac!=bc and gids[match.start()+j] is not None:
      gid=gids[match.start()+j];votes[gid][bc]+=1;examples[gid].append(a+' -> '+b)
 correction={str(k):v.most_common(1)[0][0] for k,v in votes.items() if len(v)==1}
 f=P/'label_corrections.json';old=json.loads(f.read_text(encoding='utf8')) if f.exists() else {};old.update(correction);f.write_text(json.dumps(old,ensure_ascii=False,indent=1),encoding='utf8')
 print([(k,labels.get(int(k)),v,list(set(examples[int(k)]))[:3]) for k,v in correction.items()]);print('conflicts',[(k,v) for k,v in votes.items() if len(v)>1])
if __name__=='__main__':main()
