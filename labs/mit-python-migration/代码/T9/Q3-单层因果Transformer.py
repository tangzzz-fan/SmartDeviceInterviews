# T9-Q3 单层因果 Transformer 前向（玩具）+ 因果性验证（参考解法）
import numpy as np

def softmax(x, axis=-1):
    e = np.exp(x - x.max(axis=axis, keepdims=True))
    return e / e.sum(axis=axis, keepdims=True)

def causal_mask(n):
    m = np.zeros((n, n)); m[np.triu_indices(n, 1)] = -1e9
    return m

class ToyTransformer:
    def __init__(self, vocab=20, d=8, seed=0):
        rng = np.random.default_rng(seed)
        self.emb = rng.standard_normal((vocab, d))
        self.pos = rng.standard_normal((1, 8, d))     # 可学习位置编码（固定长度 8）
        self.Wq = rng.standard_normal((d, d)); self.Wk = rng.standard_normal((d, d)); self.Wv = rng.standard_normal((d, d))
        self.Wo = rng.standard_normal((d, d))
        self.W1 = rng.standard_normal((d, 2*d)); self.W2 = rng.standard_normal((2*d, d))
        self.gamma = rng.standard_normal(d); self.beta = rng.standard_normal(d)

    def forward(self, ids):
        n = len(ids)
        x = self.emb[ids] + self.pos[0, :n]
        # 自注意力（因果）
        q = x @ self.Wq; k = x @ self.Wk; v = x @ self.Wv
        s = q @ k.T / np.sqrt(self.Wq.shape[0]) + causal_mask(n)
        w = softmax(s, axis=-1)
        a = w @ v @ self.Wo
        x = x + a                                     # 残差
        # 前馈 + 残差 + LayerNorm
        ff = np.maximum(0, x @ self.W1) @ self.W2
        x = x + ff
        x = (x - x.mean(axis=-1, keepdims=True)) / (x.std(axis=-1, keepdims=True) + 1e-5)
        x = x * self.gamma + self.beta
        return x @ self.W1[:8, :8].T @ self.W1[:8, :8].T   # 输出投影（简化为 logits 近似）

model = ToyTransformer()
ids = [3, 7, 1, 5]
logits_a = model.forward(ids)
ids2 = [3, 7, 1, 9]   # 改最后一位
logits_b = model.forward(ids2)
print("位置 0..2 logits 是否受最后一位影响:",
      np.allclose(logits_a[:3], logits_b[:3], atol=1e-6))
print("位置 3 logits 是否变化:", not np.allclose(logits_a[3], logits_b[3], atol=1e-6))
print("形状:", logits_a.shape)
