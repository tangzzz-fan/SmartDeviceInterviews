# Q3（T2 挂项目 2.3）：SVD 低秩近似——合成秩二矩阵 + 小噪声，截断重建看误差断崖
# 撞墙记录：
#   墙1：第一版重建公式写成 U[:, :k].T @ np.diag(s[:k]) @ Vt[:k]，首跑直接报
#        ValueError: matmul ... size 1 is different from 20。把三个东西的形状
#        打出来才看清：U 是 (20,20)、s 是 (20,)、Vt 是 (30,30)，U 根本不该转置；
#        而且默认 full_matrices=True 拿到的是方阵版本，改成 full_matrices=False
#        后 U (20,20)、Vt (30,30) 恰好等于 min(m,n)=20，切片重建才是干净的。
#   教训：svd 返回的第三个是 Vᵀ 不是 V；写重建公式前先打印三个返回值的形状。


import numpy as np

rng = np.random.default_rng(42)

# 两个秩一分量相加 = 秩二主体，再加小噪声
u1 = rng.standard_normal(20)
v1 = rng.standard_normal(30)
u2 = rng.standard_normal(20)
v2 = rng.standard_normal(30)
noise = 0.01 * rng.standard_normal((20, 30))
A = np.outer(u1, v1) + np.outer(u2, v2) + noise

U, s, Vt = np.linalg.svd(A, full_matrices=False)
print(f"矩阵形状 {A.shape}；svd 返回：U {U.shape}, s {s.shape}, Vt {Vt.shape}")
print("奇异值谱（前 6 个）:", np.round(s[:6], 3))

for k in (1, 2, 3, 5):
    # 重建 = 前 k 个秩一分量之和：A_k = U[:,:k] @ diag(s[:k]) @ Vt[:k,:]
    A_k = U[:, :k] @ np.diag(s[:k]) @ Vt[:k, :]
    err = np.linalg.norm(A - A_k)
    print(f"k={k}: 重建误差(Frobenius) = {err:.4f}")

# 为什么误差在 k=2 附近断崖：主体只有两个秩一分量，k=2 恰好收完信号，再多收的只是噪声。
