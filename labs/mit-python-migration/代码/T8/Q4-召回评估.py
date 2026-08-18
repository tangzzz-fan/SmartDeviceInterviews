# T8-Q4 召回评估：hit@1 / hit@5 / MRR，两种切分策略对比（参考解法）
import numpy as np

def embed(text, dim=16):
    v = np.zeros(dim)
    for ch in text:
        v[ord(ch) % dim] += 1
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

def chunk_fixed(text, size=8, overlap=2):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size - overlap)]

def chunk_paragraph(text):
    return [p.strip() for p in text.split("\n") if p.strip()]

DOC = """SwiftUI 状态管理把视图当作状态的函数。@State 用于视图私有状态。
@Observable 用于跨视图共享的模型对象。状态变化时依赖它的视图自动重算。
组合优于继承：行为可以叠加，身份才需要继承。协议默认实现让组合也能复用。
"""
# 测试集：查询 → 应命中的 chunk 文本
QUERIES = [
    ("状态函数", "SwiftUI 状态管理把视图当作状态的函数"),
    ("私有状态", "@State 用于视图私有状态"),
    ("共享模型", "@Observable 用于跨视图共享的模型对象"),
    ("自动重算", "状态变化时依赖它的视图自动重算"),
    ("组合行为", "组合优于继承：行为可以叠加"),
    ("协议复用", "协议默认实现让组合也能复用"),
]

def rank(chunks, q):
    qv = embed(q)
    scored = sorted(((np.dot(embed(c), qv), i) for i, c in enumerate(chunks)), key=lambda x: -x[0])
    return [i for _, i in scored]

def evaluate(chunker):
    chunks = chunker(DOC)
    ranks = []
    for q, gold in QUERIES:
        r = rank(chunks, q)
        gold_i = next((i for i, c in enumerate(chunks) if gold in c), -1)
        ranks.append((r.index(gold_i) + 1) if gold_i in r else 999)
    hit1 = sum(1 for r in ranks if r == 1) / len(ranks)
    hit5 = sum(1 for r in ranks if r <= min(5, len(chunks))) / len(ranks)
    mrr = sum(1.0 / r for r in ranks if r < 999) / len(ranks)
    return hit1, hit5, mrr

for name, ch in [("固定+重叠", chunk_fixed), ("按段落", chunk_paragraph)]:
    h1, h5, mrr = evaluate(ch)
    print(f"{name}: hit@1={h1:.2f} hit@5={h5:.2f} MRR={mrr:.2f}")
print("\n结论: 本测试集（mock 字符特征 embedding）固定+重叠 hit@1 更高——小 chunk 噪声小；")
print("但结论不是\"哪种更好\"，而是\"必须用指标对比，不能凭感觉\"——真实语义 embedding 下可能反转，需按真实数据评估。")
