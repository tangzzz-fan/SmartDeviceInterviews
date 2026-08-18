# Q2（T3 挂项目 3.2）：手写高斯朴素贝叶斯分类器
# 「朴素」= 给定类别后各特征条件独立，联合似然 = 每维高斯密度相乘。
# 为什么不能直接连乘概率：几十个小数（每个都 <1）连乘会指数级缩小，
#   float64 下 ~700 个 0.01 量级的数相乘就下溢到 0，两类的后验全变 0，
#   比较失效。取 log 把连乘变连加，数值稳定且比较大小等价（log 单调）。
# 撞墙记录：
#   墙1：我在文件头断言「几十个密度连乘就下溢」，首跑 50 维演示结果 7.96e-68，
#        根本没到 0——float64 的底在 1e-308 附近，50 个 0.05 量级的数连乘离底还远。
#        我的数值直觉错了数量级：要 ~700 个 0.01 或 ~220 个 1e-3 才到底。扩到 400 维
#        演示才真实下溢。教训：下溢阈值要算不要猜。
#   墙3（复攻修复）：题干要求「必须用对数概率计算」，我第一版图省事用了连乘版
#        （2 维下侥幸没炸）。复攻改成对数域：log 后验 = log 先验 + Σ log 密度，
#        比较大小不需要归一化（公共分母不影响 argmax）。改后准确率不变。


import numpy as np


def make_data(rng):
    """两团二维高斯：类0 中心 (-2,-1)，类1 中心 (2,1.5)，方差不同。"""
    n0, n1 = 300, 300
    x0 = rng.normal(loc=[-2.0, -1.0], scale=[1.0, 0.6], size=(n0, 2))
    x1 = rng.normal(loc=[2.0, 1.5], scale=[0.7, 1.2], size=(n1, 2))
    X = np.vstack([x0, x1])
    y = np.array([0] * n0 + [1] * n1)
    idx = rng.permutation(len(y))
    X, y = X[idx], y[idx]
    split = int(len(y) * 0.8)
    return X[:split], y[:split], X[split:], y[split:]


def fit(X, y):
    """估计先验与每类每维的 μ、σ²。"""
    priors, mus, vars_ = {}, {}, {}
    for c in (0, 1):
        Xc = X[y == c]
        priors[c] = len(Xc) / len(y)
        mus[c] = Xc.mean(axis=0)
        vars_[c] = Xc.var(axis=0) + 1e-6
    return priors, mus, vars_


def predict_proba(X, priors, mus, vars_):
    """对数域计算（复攻修复版）：log 后验 ∝ log 先验 + Σ_d log N(x_d|μ,σ²)，
    比较 argmax 不需要归一化；需要概率时再做 log-sum-exp 归一。"""
    log_posts = np.zeros((len(X), 2))
    for c in (0, 1):
        lp = np.full(len(X), np.log(priors[c]))
        for d in range(X.shape[1]):
            mu, var = mus[c][d], vars_[c][d]
            lp += -0.5 * np.log(2 * np.pi * var) - 0.5 * (X[:, d] - mu) ** 2 / var
        log_posts[:, c] = lp
    m = log_posts.max(axis=1, keepdims=True)          # log-sum-exp 归一
    e = np.exp(log_posts - m)
    return e / e.sum(axis=1, keepdims=True)


if __name__ == "__main__":
    rng = np.random.default_rng(11)
    Xtr, ytr, Xte, yte = make_data(rng)
    priors, mus, vars_ = fit(Xtr, ytr)
    print(f"先验估计：P(类0)={priors[0]:.3f}，P(类1)={priors[1]:.3f}")
    print(f"类0 μ={np.round(mus[0], 2)}；类1 μ={np.round(mus[1], 2)}")

    probs = predict_proba(Xte, priors, mus, vars_)
    pred = probs.argmax(axis=1)
    acc = (pred == yte).mean()
    print(f"测试集后验样例（前3行）：\n{np.round(probs[:3], 6)}")
    print(f"测试集准确率：{acc:.3f}（共 {len(yte)} 个样本）")
    assert acc > 0.95, "两团分得这么开，准确率不该这么低"

    # 高维演示：连乘下溢的真实阈值在哪？
    for D in (50, 400):
        pdfs = rng.uniform(0.01, 0.1, size=D)   # 模拟 D 个 <1 的密度值
        prod = 1.0
        for p in pdfs:
            prod *= p
        print(f"\n{D} 维连乘演示：密度连乘结果 = {prod}")
