# T9-Q1 BPE 最小实现：训练 + encode/decode 往返（参考解法）
from collections import Counter

CORPUS = ["low low low low low lower newest newest newest newest",
          "newest newest newest newest newest wide widest"]

def train_bpe(corpus, num_merges=8):
    tokens = [list(w) for w in corpus]
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for t in tokens:
            for a, b in zip(t, t[1:]):
                pairs[(a, b)] += 1
        if not pairs:
            break
        best = max(pairs, key=lambda k: pairs[k])
        merges.append(best)
        new_tokens = []
        for t in tokens:
            nt, i = [], 0
            while i < len(t):
                if i + 1 < len(t) and (t[i], t[i+1]) == best:
                    nt.append(t[i] + t[i+1]); i += 2
                else:
                    nt.append(t[i]); i += 1
            new_tokens.append(nt)
        tokens = new_tokens
    return merges, tokens

def encode(word, merges):
    t = list(word)
    changed = True
    while changed:
        changed = False
        nt, i = [], 0
        while i < len(t):
            if i + 1 < len(t) and (t[i], t[i+1]) in merges:
                nt.append(t[i] + t[i+1]); i += 2; changed = True
            else:
                nt.append(t[i]); i += 1
        t = nt
    return t

merges, _ = train_bpe(CORPUS)
print("合并序列:", merges)
for w in ["low", "lower", "newest", "widest"]:
    enc = encode(w, merges)
    dec = "".join(enc)
    print(f"{w} -> {enc} -> decode={dec} 往返一致: {w == dec}")
