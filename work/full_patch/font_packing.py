"""Reorder glyph slots to fit SLZ allocations without changing their bitmaps."""
import math,random,struct

def optimize(chars,mapping,glyphs,widths,limit,compress,glyph,iterations=30000):
    slots=sorted(mapping[ch] for ch in chars)
    bitmaps={ch:glyph(ch) for ch in chars}
    def score(order):
        gs=list(glyphs);ws=bytearray(widths)
        for code,ch in zip(slots,order):
            gs[code-1]=bitmaps[ch];ws[code-1]=6 if ord(ch)<128 else 12
        data=struct.pack('<II',len(gs),12)+ws+b''.join(gs)
        return len(compress(data,1))
    rng=random.Random(801260)
    current=list(chars);cost=score(current);best=current[:];best_cost=cost
    for step in range(iterations):
        trial=current[:];a,b=rng.sample(range(len(trial)),2)
        if step%3:
            trial[a],trial[b]=trial[b],trial[a]
        else:
            trial.insert(b,trial.pop(a))
        value=score(trial)
        temperature=max(.15,2.0*(1-(step%600)/600))
        if value<=cost or rng.random()<math.exp(min(0,(cost-value)/temperature)):
            current,cost=trial,value
        if value<best_cost:
            best,best_cost=trial[:],value
            if best_cost<=limit:
                print('Font packing fits:',best_cost,'/',limit,'after',step+1,'steps',flush=True)
                return best
        if step%300==299:
            print('Font packing:',step+1,'steps,',best_cost,'/',limit,flush=True)
            current,cost=best[:],best_cost
    raise ValueError(('font packing did not fit',best_cost,limit))
