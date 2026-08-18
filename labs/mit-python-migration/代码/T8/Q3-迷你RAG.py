# T8-Q3 迷你 RAG：切分 → mock embedding → top-k → 组装上下文（参考解法）
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

def retrieve(chunks, query, k=2):
    qv = embed(query)
    scored = sorted(((np.dot(embed(c), qv), c) for c in chunks), key=lambda x: -x[0])
    return [c for _, c in scored[:k]]

def assemble(chunks, query, max_tokens=40):
    hits = retrieve(chunks, query)
    ctx = "\n".join(hits)
    budget = ctx.split()[:max_tokens]
    return f"[上下文]\n{' '.join(budget)}\n[问题] {query}"

doc = """SwiftUI 状态管理把视图当作状态的函数。@State 用于视图私有状态。
@Observable 用于跨视图共享的模型对象。状态变化时依赖它的视图自动重算。
组合优于继承：行为可以叠加，身份才需要继承。协议默认实现让组合也能复用。
"""
query = "共享的模型对象怎么管理"

for name, chunker in [("固定+重叠", chunk_fixed), ("按段落", chunk_paragraph)]:
    chunks = chunker(doc)
    ctx = assemble(chunks, query)
    print(f"=== {name} 切分 ===")
    print(f"chunk 数: {len(chunks)}")
    print(ctx[:120])
    print()
