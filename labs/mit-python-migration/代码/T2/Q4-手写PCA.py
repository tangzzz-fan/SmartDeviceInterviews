# Q4（T2 挂项目 2.4）：手写 PCA——协方差矩阵 + eigh，与 SVD 交叉验证第一主成分
# 撞墙记录：
#   墙1：首跑输出特征值 [0.1523, 3.4259]、「方差解释比 = 0.043」——第一主成分
#        只解释 4% 方差，明显不对。原来 np.linalg.eigh 返回的特征值是升序的，
#        vecs[:, 0] 是最小特征值方向！加 argsort 反转排序后解释比 0.957，正常了。
#   墙2：SVD 交叉验证第一版拿 U_[:, 0]（长 600，样本空间的向量）去和 w1（长 2）
#        做点积，报 ValueError: size 2 is different from 600。想明白：数据在特征
#        空间的方向藏在 Vt 的行里（X_c ≈ U diag(s) Vt，Vt 第 i 行才是第 i 主成分
#        方向），改用 Vt_[0] 后对上。
#   墙3（预判式）：特征向量方向可差一个负号，比对前先按点积符号对齐，否则
#        同一方向会误判为不一致。
# 直觉一句话：投影到方向 w 后的方差是 wᵀCw，要最大化它（||w||=1），
#             拉格朗日求导直接得到 Cw = λw——最优方向就是最大特征值对应的特征向量。


import numpy as np

rng = np.random.default_rng(7)
N = 600

# 带相关性的二维点云：x 拉伸 2 倍后旋转 30°，第二维只留小方差
base = rng.standard_normal((N, 2)) * np.array([2.0, 0.4])
theta = np.deg2rad(30)
R = np.array([[np.cos(theta), -np.sin(theta)],
              [np.sin(theta), np.cos(theta)]])
X = base @ R.T

# 1) 中心化
X_c = X - X.mean(axis=0)

# 2) 协方差矩阵 + 特征分解
C = X_c.T @ X_c / (N - 1)
vals, vecs = np.linalg.eigh(C)
idx = np.argsort(vals)[::-1]        # eigh 返回升序，主成分要最大特征值，反转！
vals, vecs = vals[idx], vecs[:, idx]
w1 = vecs[:, 0]                     # 第一主成分 = 最大特征值对应的特征向量
ratio = vals[0] / vals.sum()
print(f"特征值：{np.round(vals, 4)}")
print(f"第一主成分方向 w1 = {np.round(w1, 4)}")
print(f"投影到 w1 的方差 = {(X_c @ w1).var():.4f}")
print(f"方差解释比 = {ratio:.3f}")

# 3) SVD 交叉验证
U_, s_, Vt_ = np.linalg.svd(X_c, full_matrices=False)
u1 = Vt_[0]                         # 数据空间的方向在 Vt 的行里，不是 U 的列
if u1 @ w1 < 0:
    u1 = -u1                        # 允许符号相反，对齐后再比
print(f"SVD 方向（对齐符号后） = {np.round(u1, 4)}")
assert np.allclose(u1, w1, atol=1e-6), "两法方向不一致"
print("交叉验证通过：协方差特征分解与 SVD 的第一主成分方向一致")
