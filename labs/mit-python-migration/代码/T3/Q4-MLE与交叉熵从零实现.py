# Q4（T3 挂项目 3.4）：MLE 与交叉熵从零实现——伯努利 MLE 网格搜索 + 手写交叉熵
# 撞墙记录：
#   墙1：第一版 cross_entropy 漏了外层负号（写成 z[labels] − log Σexp(z)），首跑输出
#        CE = -0.4644——损失为负就已经不对劲，接着「正确类更有信心损失该更小」的
#        断言直接报错（-0.0290 > -0.4644，方向反了）。补上负号后全部通过。
#        教训：损失的符号/单调性性质验证比背公式可靠——性质断言当场抓住符号错。


import numpy as np


def bernoulli_log_likelihood(p, k, n):
    """n 次试验 k 次成功的对数似然：k·ln(p) + (n-k)·ln(1-p)。"""
    return k * np.log(p) + (n - k) * np.log(1 - p)


def cross_entropy(logits, labels):
    """类别分布交叉熵（单样本）：-log(softmax(logits)[label])。"""
    z = logits - logits.max()          # 减最大值稳定化
    return -(z[labels] - np.log(np.exp(z).sum()))   # 外层负号：−log(p_y)


if __name__ == "__main__":
    rng = np.random.default_rng(27)

    # ① 伯努利 MLE：网格搜索找最大对数似然的 p̂
    n = 1000
    true_p = 0.62
    data = rng.binomial(1, true_p, size=n)
    k = int(data.sum())
    freq = k / n
    print(f"试验 n={n}，成功 k={k}，样本频率 = {freq:.4f}（真实 p = {true_p}）")

    grid = np.linspace(0.01, 0.99, 9901)
    ll = np.array([bernoulli_log_likelihood(p, k, n) for p in grid])
    p_hat = grid[ll.argmax()]
    print(f"网格搜索 MLE：p̂ = {p_hat:.4f}（理论应 = 样本频率）")
    assert abs(p_hat - freq) < 0.01, "MLE 应和样本频率一致到小数点后两位"

    # ② 手写交叉熵三性质验证
    logits = np.array([2.0, 1.0, 0.5])
    label = 0
    ce_base = cross_entropy(logits, label)
    print(f"\n交叉熵基准：logits={logits}，正确类=0，CE = {ce_base:.4f}")

    # 性质1：正确类 logit 越大，损失越小
    ce_up = cross_entropy(logits + np.array([3.0, 0, 0]), label)
    print(f"正确类 logit +3 后：CE = {ce_up:.4f}（应变小）")
    assert ce_up < ce_base, "正确类更有信心，损失该更小"

    # 性质2：损失非负
    for _ in range(100):
        z = rng.uniform(-5, 5, size=4)
        assert cross_entropy(z, rng.integers(0, 4)) >= 0, "交叉熵不该为负"
    print("100 组随机 logits 交叉熵全部非负 ✓")

    # 性质3：均匀 logits 时 CE = log(类别数)
    K = 5
    ce_uniform = cross_entropy(np.zeros(K), 2)
    print(f"均匀 logits（K={K}）：CE = {ce_uniform:.4f}，log(K) = {np.log(K):.4f}")
    assert abs(ce_uniform - np.log(K)) < 1e-9, "均匀时交叉熵应等于 log K"
    print("三性质全部验证通过 ✓")
