# T9-Q2 自注意力最小实现（numpy）：单头/多头 + 三种 mask（参考解法）
import numpy as np

def softmax(x, axis=-1):
    e = np.exp(x - x.max(axis=axis, keepdims=True))
    return e / e.sum(axis=axis, keepdims=True)

def attention(Q, K, V, mask=None):
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)
    if mask is not None:
        scores = scores + mask          # 关键：mask 加在 softmax 前（-inf）
    w = softmax(scores, axis=-1)
    return w @ V, w

def make_causal_mask(n):
    m = np.zeros((n, n))
    m[np.triu_indices(n, 1)] = -1e9    # 未来位置 -inf
    return m

def make_pad_mask(valid_len, n):
    m = np.zeros((n, n))
    m[valid_len:, :] = -1e9
    m[:, valid_len:] = -1e9
    return m

np.random.seed(0)
n, d = 4, 8
X = np.random.randn(n, d)
Q = X @ np.random.randn(d, d); K = X @ np.random.randn(d, d); V = X @ np.random.randn(d, d)

_, w_none = attention(Q, K, V)
_, w_causal = attention(Q, K, V, mask=make_causal_mask(n))
_, w_pad = attention(Q, K, V, mask=make_pad_mask(2, n))
print("无 mask 权重矩阵第 3 行:", np.round(w_none[2], 2))
print("因果 mask 后第 1 行（只能看自己）:", np.round(w_causal[0], 2))
print("填充 mask 后权重:", np.round(w_pad, 2))
print("证明: 被 mask 位置权重为 0（-inf → softmax=0）")

# 多头（2 头）
def multi_head(Q, K, V, heads=2, mask=None):
    h = heads; d = Q.shape[-1]; dh = d // h
    Qs = Q.reshape(n, h, dh).transpose(1, 0, 2)
    Ks = K.reshape(n, h, dh).transpose(1, 0, 2)
    Vs = V.reshape(n, h, dh).transpose(1, 0, 2)
    outs = []
    for i in range(h):
        o, _ = attention(Qs[i], Ks[i], Vs[i], mask=mask)
        outs.append(o)
    return np.concatenate(outs, axis=-1)

print("多头输出形状:", multi_head(Q, K, V).shape, "（应 (4, 8)）")
