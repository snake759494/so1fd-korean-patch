from pathlib import Path
import json,re,time,sys
P=Path(__file__).parent
GLOSSARY={
'ラティ':'라티','ミリー':'밀리','ドーン':'돈','ロニキス':'로니키스','イリア':'이리아','シウス':'시우스','アシュレイ':'애슐리','フィア':'피아','ヨシュア':'요슈아','マーヴェル':'마벨','ティニーク':'티니크','ペリシー':'페리시','ウェルチ':'웰치','エリス':'에리스','エクダート':'에크다트','ローク':'로크','クラトス':'크라토스','クール':'쿠르','メトークス':'메토크스','メトークス橋':'메토크스 다리','メトークス山':'메토크스 산','メトークス山頂':'메토크스 산 정상','ポートミス':'포트미스','オタニム':'오타님','タトローイ':'타트로이','アストラル':'아스트랄','トロップ':'트로프','イオニス':'이오니스','ヴァン':'반','シルヴァラント':'실바란트','ムーア':'무어','フォル':'폴','所持金':'소지금','戦闘結果':'전투 결과','経験値':'경험치','ヒール':'힐','ローズヒップ':'로즈힙','スペクタクルズ':'스펙터클즈','を手に入れた。':'을(를) 얻었다.','を入手しました。':'을(를) 얻었다.','手に入れた。':'을(를) 얻었다.','しかし、これ以上持てなかった…。':'하지만 더는 지닐 수 없었다…','はい':'예','いいえ':'아니요','キャンセル':'취소','泊まる':'묵는다','泊まらない':'묵지 않는다'
}
JP_FIX={'真寒の瞳':'真実の瞳','寒桜花奥義':'裏桜花奥義','天便':'天使','便う':'使う','便える':'使える','恩います':'思います','恩う':'思う','恩って':'思って','故期':'故郷','説明良':'説明員','閃き':'聞き','閃く':'聞く','閃か':'聞か','戦闘良け':'戦闘負け'}
def norm(s):
 for a,b in JP_FIX.items():s=s.replace(a,b)
 return s.strip().replace('　',' ')
def segments():
 d=json.loads((P/'field_readable.json').read_text(encoding='utf8'));out={}
 for x in d:
  for s in re.split(r'\{[0-9a-f]+\}',x['jp']):
   s=norm(s)
   if s and re.search(r'[\u3040-\u30ff\u3400-\u9fff]',s):out[s]=None
 return list(out)
def main():
 import ctranslate2
 from transformers import AutoTokenizer
 cache=P/'translation_cache.json';done=json.loads(cache.read_text(encoding='utf8')) if cache.exists() else {}
 from build_fields import load_cache
 done.update(load_cache())
 done.update(GLOSSARY)
 todo=[s for s in segments() if s not in done]
 (P/'translation_queue.json').write_text(json.dumps(todo,ensure_ascii=False,indent=1),encoding='utf8')
 tok=AutoTokenizer.from_pretrained(P/'nllb_tokenizer',src_lang='jpn_Jpan')
 tr=ctranslate2.Translator(str(P/'nllb_ct2'),device='cpu',compute_type='int8',intra_threads=2)
 start=time.time()
 for i in range(0,len(todo),24):
  batch=todo[i:i+24]
  inp=[tok.convert_ids_to_tokens(tok.encode(s)) for s in batch]
  if any(len(x)>500 for x in inp):raise ValueError('oversized source segment')
  out=tr.translate_batch(inp,target_prefix=[['kor_Hang']]*len(batch),beam_size=2,max_decoding_length=256,repetition_penalty=1.05,no_repeat_ngram_size=4)
  for s,r in zip(batch,out):done[s]=tok.decode(tok.convert_tokens_to_ids(r.hypotheses[0]),skip_special_tokens=True).strip()
  tmp=cache.with_suffix('.tmp');tmp.write_text(json.dumps(done,ensure_ascii=False,indent=1),encoding='utf8');tmp.replace(cache)
  print(i+len(batch),'/',len(todo),'seconds',round(time.time()-start),flush=True)
 print('DONE',len(done),flush=True)
if __name__=='__main__':main()
