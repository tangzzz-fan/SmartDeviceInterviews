"""
T4-Q2 torch 训练循环迁移 + 与 Q1 手写梯度对拍（挂项目 4.2）

参数收集机制（作答稿 C2 展开）：nn.Module 的 __setattr__ 拦截赋值，
nn.Parameter 进 _parameters 字典、子 Module 进 _modules 字典；parameters()
递归这两张字典收集。普通 torch.tensor 赋给属性不会被收集。
nn.Linear 的参数注册：weight 是 nn.Parameter，形状 (out_features, in_features)，
forward 里算 y = x @ weight.T + bias —— 权重存的是「转置」。

撞墙记录：
  墙1（真实翻车）：第一版照搬 Q1 的 W1（形状 (4,8)）直接 copy_ 进
  fc1.weight，首跑当场报：
  RuntimeError: The size of tensor a (4) must match the size of tensor b (8)
  at non-singleton dimension 1
  根因：nn.Linear 的 weight 形状是 (out, in) = (8, 4)，forward 里自己转置；
  我拿 numpy 心智「权重就是 (in, out)」直接套。修复：fc1/fc2 都 copy_(W.T)。
  教训：换框架先 print 一遍参数形状，别拿旧心智猜布局。
  墙2（真实翻车）：修完形状再跑，前向当场报：
  RuntimeError: mat1 and mat2 must have the same dtype, but got Double and Float
  根因：numpy 默认 float64 → torch.tensor 转出来是 Double，而 nn.Linear
  参数默认 float32。Swift 里类型不匹配编译器当场拦，torch 拖到运行时。
  修复：model.double() + 输入显式 float64，与 numpy 数值对拍也免精度差。
"""
import numpy as np
import torch
import torch.nn as nn

# ---------- 与 Q1 完全同源的初始化（同 seed 同顺序） ----------
rng = np.random.default_rng(0)
N, D_IN, H, D_OUT = 5, 4, 8, 2
X_np = rng.standard_normal((N, D_IN))
y_np = rng.integers(0, D_OUT, size=N)
W1 = rng.standard_normal((D_IN, H)) * 0.5
b1 = np.zeros(H)
W2 = rng.standard_normal((H, D_OUT)) * 0.5
b2 = np.zeros(D_OUT)


# ---------- Q1 的手写梯度（对拍基准） ----------
def numpy_grads():
    h_pre = X_np @ W1 + b1
    h = np.maximum(h_pre, 0.0)
    z = h @ W2 + b2
    z_s = z - z.max(axis=1, keepdims=True)
    p = np.exp(z_s) / np.exp(z_s).sum(axis=1, keepdims=True)
    dz = p.copy()
    dz[np.arange(N), y_np] -= 1.0
    dz /= N
    dW2 = h.T @ dz
    db2 = dz.sum(axis=0)
    dh_pre = (dz @ W2.T) * (h_pre > 0)
    dW1 = X_np.T @ dh_pre
    db1 = dh_pre.sum(axis=0)
    return dW1, db1, dW2, db2


# ---------- torch 版 MLP ----------
class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(D_IN, H)
        self.fc2 = nn.Linear(H, D_OUT)

    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))


torch.manual_seed(0)
model = MLP().double()                              # 墙2 修复：参数也升 float64
with torch.no_grad():
    model.fc1.weight.copy_(torch.tensor(W1.T))      # 墙1 修复：weight 存 (out, in)
    model.fc1.bias.copy_(torch.tensor(b1))
    model.fc2.weight.copy_(torch.tensor(W2.T))
    model.fc2.bias.copy_(torch.tensor(b2))

X = torch.tensor(X_np, dtype=torch.float64)
y = torch.tensor(y_np)

# ---------- 梯度对拍：同输入一次前向 ----------
opt = torch.optim.SGD(model.parameters(), lr=0.1)
opt.zero_grad()
loss = nn.functional.cross_entropy(model(X), y)
loss.backward()

dW1_np, db1_np, dW2_np, db2_np = numpy_grads()
pairs = [
    ("dW1", model.fc1.weight.grad.T.numpy(), dW1_np),   # weight 存转置，比的时候转回来
    ("db1", model.fc1.bias.grad.numpy(), db1_np),
    ("dW2", model.fc2.weight.grad.T.numpy(), dW2_np),
    ("db2", model.fc2.bias.grad.numpy(), db2_np),
]
worst = 0.0
for name, g_torch, g_np in pairs:
    err = float(np.abs(g_torch - g_np).max() / np.maximum(1.0, np.abs(g_np).max()))
    worst = max(worst, err)
    print(f"{name}: torch vs 手写 最大相对误差 = {err:.2e}")
print(f"对拍最大相对误差 = {worst:.2e}")
assert worst < 1e-5, f"对拍失败：{worst:.2e} >= 1e-5"
print("梯度对拍通过：autograd 与手推反向传播一致 ✓")

# ---------- 五步训练循环（同一批数据 100 步） ----------
losses = []
for step in range(100):
    logits = model(X)                                # 1 forward
    loss = nn.functional.cross_entropy(logits, y)    # 2 loss
    opt.zero_grad()                                  # 3 zero_grad（清累加）
    loss.backward()                                  # 4 backward（图上遍历算 grad）
    opt.step()                                       # 5 step（用 grad 更新 param）
    losses.append(loss.item())                       # item() 切图引用，防显存泄漏
print(f"训练 loss：首步 {losses[0]:.6f} → 末步 {losses[-1]:.6f}")
assert losses[-1] < losses[0], "loss 没下降，训练循环有问题"
print("loss 单调下降断言通过 ✓")
