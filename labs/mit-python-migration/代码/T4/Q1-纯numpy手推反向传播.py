"""
T4-Q1 纯 Python/numpy 手推反向传播（挂项目 4.1）

文件头推导链（链式法则每一环）：
  前向：h_pre = X W1 + b1 ; h = relu(h_pre) ; z = h W2 + b2 ; p = softmax(z)
  损失：L = mean_i( -log p[i, y_i] )
  反向：
    ∂L/∂z    = (p − onehot(y)) / N            （softmax+CE 打包后的经典结果，T3-Q4 推过）
    ∂L/∂W2   = hᵀ · ∂L/∂z                     （z = h W2 + b2，对 W2 求导留左因子转置）
    ∂L/∂b2   = Σ_i ∂L/∂z[i]                   （bias 每样本加一次，梯度沿 batch 求和）
    ∂L/∂h    = ∂L/∂z · W2ᵀ                    （梯度回传乘权重转置）
    ∂L/∂h_pre = ∂L/∂h ⊙ relu'(h_pre)          （ReLU 门：>0 放行，≤0 截断）
    ∂L/∂W1   = Xᵀ · ∂L/∂h_pre
    ∂L/∂b1   = Σ_i ∂L/∂h_pre[i]

撞墙记录：
  墙1（真实翻车）：第一版反向把 ∂L/∂h 直接当 ∂L/∂h_pre 用——忘了乘 ReLU 门
  （心里把 relu 当「没梯度影响的东西」滑过去了）。首跑数值对拍当场露馅：
  W1/b1 抽查点相对误差 5.13e-03 ~ 2.80e-01（如 W1[3,7] 手写 +0.2533 vs 数值
  +0.0867），W2/b2 却全对到 1e-10（因为门在 W2 下游）——断在哪一环证据清清楚楚。
  AssertionError: 对拍失败：最大相对误差 2.80e-01 >= 1e-5
  修复：dh_pre = dh * (h_pre > 0)。教训：每一环都写出来才叫链式法则，
  「显然」的那一环往往就是断环。
  无其他墙：对拍框架沿用 T3-Q4 的性质断言纪律（相对误差 < 1e-5 才许交）。
"""
import numpy as np

rng = np.random.default_rng(0)
N, D_IN, H, D_OUT = 5, 4, 8, 2

X = rng.standard_normal((N, D_IN))
y = rng.integers(0, D_OUT, size=N)
W1 = rng.standard_normal((D_IN, H)) * 0.5
b1 = np.zeros(H)
W2 = rng.standard_normal((H, D_OUT)) * 0.5
b2 = np.zeros(D_OUT)


def forward(X, W1, b1, W2, b2):
    h_pre = X @ W1 + b1
    h = np.maximum(h_pre, 0.0)
    z = h @ W2 + b2
    z_s = z - z.max(axis=1, keepdims=True)          # 稳定化（T3-Q3 纪律）
    e = np.exp(z_s)
    p = e / e.sum(axis=1, keepdims=True)
    return p, (h_pre, h)


def loss_fn(p, y):
    return -np.log(p[np.arange(len(y)), y]).mean()


def backward(X, y, W2, p, h_pre, h):
    n = len(y)
    dz = p.copy()
    dz[np.arange(n), y] -= 1.0
    dz /= n                                          # mean 损失的 1/N
    dW2 = h.T @ dz
    db2 = dz.sum(axis=0)
    dh = dz @ W2.T
    dh_pre = dh * (h_pre > 0)                        # ReLU 门（墙1 修复点）
    dW1 = X.T @ dh_pre
    db1 = dh_pre.sum(axis=0)
    return dW1, db1, dW2, db2


def numeric_grad(param, idx, loss_at):
    """中心差分：(f(x+e) − f(x−e)) / 2e"""
    eps = 1e-6
    saved = param[idx]
    param[idx] = saved + eps
    lp = loss_at()
    param[idx] = saved - eps
    lm = loss_at()
    param[idx] = saved
    return (lp - lm) / (2 * eps)


def rel_err(a, b):
    return abs(a - b) / max(1.0, abs(a), abs(b))


def full_loss():
    p, _ = forward(X, W1, b1, W2, b2)
    return loss_fn(p, y)


p, (h_pre, h) = forward(X, W1, b1, W2, b2)
dW1, db1, dW2, db2 = backward(X, y, W2, p, h_pre, h)

print(f"loss = {loss_fn(p, y):.6f}")
checks = [
    ("W1", W1, dW1, [(0, 0), (3, 7), (2, 4)]),
    ("b1", b1, db1, [(2,), (7,)]),
    ("W2", W2, dW2, [(5, 1), (0, 0)]),
    ("b2", b2, db2, [(1,), (0,)]),
]
worst = 0.0
for name, param, grad, idxs in checks:
    for idx in idxs:
        ng = numeric_grad(param, idx, full_loss)
        err = rel_err(grad[idx], ng)
        worst = max(worst, err)
        print(f"{name}{list(idx)}: 手写 = {grad[idx]:+.8f}  数值 = {ng:+.8f}  相对误差 = {err:.2e}")
print(f"最大相对误差 = {worst:.2e}")
assert worst < 1e-5, f"对拍失败：最大相对误差 {worst:.2e} >= 1e-5"
print("全部断言通过：手写梯度与数值梯度一致 ✓")
