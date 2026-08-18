# Q2（T2 挂项目 2.1）：二维线性变换可视化——旋转 90°/剪切/投影，验证「列 = 基向量去向」
# 撞墙记录：
#   墙1：第一版 ROT90 凭记忆写成 [[0,1],[-1,0]]，首跑断言就把我拦住了——
#        e1=(1,0) 落到了 (0,-1)（这是顺时针）。逆时针 90° 应把 e1 送到 (0,1)、
#        e2 送到 (-1,0)，改为 [[0,-1],[1,0]] 后通过。教训：矩阵写对写错，
#        用「基向量落到哪」当验收标准，一眼可见。


import numpy as np

ROT90 = np.array([[0, -1],
                  [1, 0]])    # 逆时针 90°：e1→(0,1)，e2→(-1,0)
SHEAR = np.array([[1, 1],
                  [0, 1]])
PROJ_X = np.array([[1, 0],
                   [0, 0]])

# 「L」形点云：竖直三格 + 底边向右一格
POINTS = np.array([[0, 0], [0, 1], [0, 2], [1, 0], [2, 0], [3, 0]])


def render(pts, title, lo=-4, hi=4, W=17, H=9):
    """简易 ASCII 网格：x 向右、y 向上。"""
    sx = lambda x: round((x - lo) / (hi - lo) * (W - 1))
    sy = lambda y: round((hi - y) / (hi - lo) * (H - 1))
    grid = [["."] * W for _ in range(H)]
    for x, y in pts:
        c, r = sx(x), sy(y)
        if 0 <= c < W and 0 <= r < H:
            grid[r][c] = "#"
    print(f"--- {title} ---")
    print("\n".join("".join(row) for row in grid))


def apply(T, pts):
    return pts @ T.T     # 每个点作为行向量左乘 T^T，等价于 T 作用于列向量


if __name__ == "__main__":
    render(POINTS, "原始 L")

    # 预期检查：逆时针旋转 90° 应把 e1=(1,0) 送到 (0,1)
    e1 = ROT90 @ np.array([1, 0])
    e2 = ROT90 @ np.array([0, 1])
    print(f"ROT90 作用于 e1 = {e1}，期望 (0, 1)")
    assert np.array_equal(e1, [0, 1]), "e1 落点不对，旋转矩阵有问题"

    for name, T in [("旋转 90°", ROT90), ("剪切", SHEAR), ("投影到 x 轴", PROJ_X)]:
        render(apply(T, POINTS), name)
        # M3 核心论断：变换后的基向量 == 矩阵的两列
        assert np.allclose(T @ np.array([1, 0]), T[:, 0]), f"{name}: T@e1 != 第 1 列"
        assert np.allclose(T @ np.array([0, 1]), T[:, 1]), f"{name}: T@e2 != 第 2 列"
    print("断言通过：三个变换都有 T@e_j == 第 j 列（列 = 基向量的去向）")
