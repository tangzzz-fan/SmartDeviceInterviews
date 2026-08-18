"""
T4-Q4 Dataset/DataLoader 管道（挂项目 4.4）

职责分界：
  Dataset 管「第 i 个样本是什么」（__len__ / __getitem__，单样本级）；
  DataLoader 管「怎么把样本组成 batch」（batch_size / shuffle / 并行 / collate）。
collate_fn：给每个样本附加权重 w = 1 + 0.5*label（非平凡合并：堆叠 X、
拼 labels、拼 weights），训练用加权交叉熵。

撞墙记录：
  墙1（真实翻车）：对拍判据第一版用「各 batch 平均 loss 的简单平均」对
  「全量前向 loss」——N=60、batch=8 时最后一个 batch 只有 4 个样本，
  简单平均把小 batch 抬得太重，首跑实测 0.7170448039 vs 0.7180694867，
  差 1e-3 量级当场失败：
  AssertionError: batch 加权平均 loss 与全量 loss 不一致
  修复分两步（两次真翻车）：先改成按 batch 内样本数加权——还是不一致
  （0.7161833479 vs 0.7180694867）！再想才明白：batch loss 的分母是
  该 batch 的 Σw 而不是样本数 n，重建全量要按 ws.sum() 加权：
  Σ_batches (Σw)_b·L_b = Σ_all wᵢ·ceᵢ，除以 Σ_all wᵢ 才严格相等。
  教训：涉及「平均的平均」先写出每一份的分子分母再合并，别拍脑袋选权重。
"""
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# ---------- 数据源（与 Q1/Q2 风格一致，量放大到 60） ----------
rng = np.random.default_rng(42)
N_SAMPLES, D_IN, H, D_OUT = 60, 4, 8, 2
X_ALL = rng.standard_normal((N_SAMPLES, D_IN)).astype(np.float64)
Y_ALL = rng.integers(0, D_OUT, size=N_SAMPLES)


class WeightedBlobDataset(Dataset):
    """Dataset 职责：只回答『一共多少个、第 i 个是什么』"""

    def __init__(self, X, y):
        self.X, self.y = X, y

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        return self.X[i], int(self.y[i])


def weighted_collate(batch):
    """DataLoader 的合并钩子：堆叠特征、拼标签、按标签附加样本权重"""
    xs = torch.tensor(np.stack([b[0] for b in batch]), dtype=torch.float64)
    ys = torch.tensor([b[1] for b in batch])
    ws = 1.0 + 0.5 * ys.to(torch.float64)           # 非平凡：权重随 label 变
    return xs, ys, ws


class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(D_IN, H)
        self.fc2 = nn.Linear(H, D_OUT)

    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))


def weighted_ce(model, xs, ys, ws):
    per = nn.functional.cross_entropy(model(xs), ys, reduction="none")
    return (per * ws).sum() / ws.sum()


# ---------- 判据①：shuffle 的 seed 可复现 ----------
ds = WeightedBlobDataset(X_ALL, Y_ALL)


def batch_order(seed):
    g = torch.Generator().manual_seed(seed)
    loader = DataLoader(ds, batch_size=8, shuffle=True,
                        generator=g, collate_fn=weighted_collate)
    return [tuple(b[1].tolist()) for b in loader]


o1, o1b, o2 = batch_order(42), batch_order(42), batch_order(7)
assert o1 == o1b, "同 seed 两遍顺序应一致"
assert o1 != o2, "不同 seed 顺序应不同"
print(f"判据①：seed=42 两遍顺序一致、seed=7 不同 ✓（共 {len(o1)} 个 batch，末批 {len(o1[-1])} 个样本）")

# ---------- 判据②：逐 batch 加权平均 loss == 全量前向 loss ----------
torch.manual_seed(0)
model = MLP().double()
model.eval()
with torch.no_grad():
    loader = DataLoader(ds, batch_size=8, shuffle=False, collate_fn=weighted_collate)
    num = den = 0.0
    for xs, ys, ws in loader:
        l = weighted_ce(model, xs, ys, ws)
        num += l.item() * ws.sum().item()           # 墙1 终修：按权重和加权
        den += ws.sum().item()
    batch_avg = num / den
    full = weighted_ce(model, torch.tensor(X_ALL), torch.tensor(Y_ALL),
                       1.0 + 0.5 * torch.tensor(Y_ALL, dtype=torch.float64)).item()
print(f"判据②：逐 batch 加权平均 = {batch_avg:.10f}，全量前向 = {full:.10f}")
assert abs(batch_avg - full) < 1e-12, "batch 加权平均 loss 与全量 loss 不一致"
print("对拍一致 ✓")

# ---------- 训练：5 个 epoch ----------
torch.manual_seed(0)
model = MLP().double()
opt = torch.optim.SGD(model.parameters(), lr=0.1)
first = last = None
for epoch in range(5):
    g = torch.Generator().manual_seed(epoch)
    loader = DataLoader(ds, batch_size=8, shuffle=True,
                        generator=g, collate_fn=weighted_collate)
    tot, cnt = 0.0, 0
    for xs, ys, ws in loader:
        opt.zero_grad()
        loss = weighted_ce(model, xs, ys, ws)
        loss.backward()
        opt.step()
        tot += loss.item() * len(ys)
        cnt += len(ys)
    avg = tot / cnt
    if epoch == 0:
        first = avg
    last = avg
    print(f"epoch {epoch + 1}: 加权平均 loss = {avg:.6f}")
assert last < first, "loss 没下降"
print(f"训练完成：loss {first:.6f} → {last:.6f} ✓")
