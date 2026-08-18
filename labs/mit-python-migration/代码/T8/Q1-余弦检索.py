# T8-Q1 numpy 余弦相似度 + 精确 top-k（参考解法）
import numpy as np

def embed(text, dim=16):
    v = np.zeros(dim)
    for ch in text:
        v[ord(ch) % dim] += 1
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

corpus = [
    "Swift 语言学习笔记", "SwiftUI 状态管理入门", "Python 异步编程", "设计模式基础",
    "Combine 响应式编程", "iOS 网络层封装", "任务清单 App", "模型推理部署",
    "机器学习基础", "数据库索引优化",
]

def cosine_topk(q, k=3):
    qv = embed(q)
    scored = sorted(((np.dot(embed(d), qv), i, d) for i, d in enumerate(corpus)), key=lambda x: -x[0])
    return scored[:k]

for q in ["Swift 编程", "网络请求"]:
    print(f"query: {q}")
    for s, i, d in cosine_topk(q):
        print(f"  {s:.3f}  {d}")
