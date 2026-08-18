# Q1（T3 挂项目 3.1）：蒙特卡洛验证大数定律与中心极限定理
# 撞墙记录：无（刷题舒适区，一次写对；唯一的犹豫是 CLT 验证用什么量化证据，
#           最后选了「样本均值的均值/标准差对拍理论值 + 2.5/50/97.5 分位数对比」）。

import numpy as np

rng = np.random.default_rng(2026)

# 不均匀骰子：面值 1..6，概率不均
faces = np.array([1, 2, 3, 4, 5, 6])
probs = np.array([0.05, 0.10, 0.15, 0.20, 0.25, 0.25])
mu = float((faces * probs).sum())                    # 真期望
var = float(((faces - mu) ** 2 * probs).sum())       # 真方差
sigma = var ** 0.5
print(f"骰子分布：真期望 μ = {mu:.3f}，σ = {sigma:.3f}")

# ① LLN：样本均值随 N 收敛
print("\n--- ① 大数定律：样本均值随 N 收敛 ---")
for N in (10, 100, 1000, 10000, 100000):
    samples = rng.choice(faces, size=N, p=probs)
    print(f"N={N:>6}: 样本均值 = {samples.mean():.4f}（μ = {mu:.3f}）")

# ② CLT：固定 N=30，重复 10000 次，样本均值的分布 ≈ N(μ, σ²/N)
print("\n--- ② 中心极限定理：N=30 重复 10000 次 ---")
N, R = 30, 10000
means = np.array([rng.choice(faces, size=N, p=probs).mean() for _ in range(R)])
theory_std = sigma / np.sqrt(N)
print(f"这堆均值的均值   = {means.mean():.4f}（理论 μ      = {mu:.3f}）")
print(f"这堆均值的标准差 = {means.std():.4f}（理论 σ/√N  = {theory_std:.4f}）")

q = np.percentile(means, [2.5, 50, 97.5])
theory_q = [mu - 1.96 * theory_std, mu, mu + 1.96 * theory_std]   # 正态近似分位数
print(f"实测分位数 [2.5%, 50%, 97.5%] = {np.round(q, 4)}")
print(f"理论分位数（正态近似）        = {np.round(theory_q, 4)}")
assert abs(means.mean() - mu) < 0.02, "均值偏离理论太远"
assert abs(means.std() - theory_std) < 0.02, "标准差偏离 σ/√N 太远"
assert np.allclose(q, theory_q, atol=0.03), "分位数与正态近似对不上"
print("结论：样本均值分布的均值/标准差/分位数都与 N(μ, σ²/N) 理论值对上，CLT 验证通过")
