from translate_local import *
import ctranslate2
from transformers import AutoTokenizer
tok=AutoTokenizer.from_pretrained(P/'nllb_tokenizer',src_lang='jpn_Jpan');tr=ctranslate2.Translator(str(P/'nllb_ct2'),device='cpu',compute_type='int8',intra_threads=2)
ss=['やっぱり肉まん。ふかふかもちもち…。','ぎょーざ…。あっ、でもニンニクは抜いて…。','ふはは。そう解釈したほうが本人のためなのか。なにごともおぼれてはイカン。','皆と旅ができて楽しかった。','この絵画に刻まれた暖かな息吹は見たもの全員の心と体を優しく癒すという','初めまして。私の名前はラティです。']
for s in ss:
 r=tr.translate_batch([tok.convert_ids_to_tokens(tok.encode(s))],target_prefix=[['kor_Hang']],beam_size=4,max_decoding_length=256)[0]
 print(s,'=>',tok.decode(tok.convert_tokens_to_ids(r.hypotheses[0]),skip_special_tokens=True),flush=True)
