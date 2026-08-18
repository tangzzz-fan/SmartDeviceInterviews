# Q1（T2 挂项目 2.1）：纯 Python 手写 matmul，与 numpy 对拍 + 耗时对比
# 撞墙记录：
#   墙1：第一版形状检查写成了 len(A) != len(B[0])（行数对列数），(2,3)@(3,2) 的合法
#        乘法直接被拒；打印两个矩阵形状才发现检查的是错的维度，改为 cols_a != rows_b。
#   墙2：耗时对比第一次只跑一遍，两次运行数字抖动很大没法下结论，改成 3 遍取平均。
#   注：结果矩阵初始化用列表推导式每行独立新建（T1 复攻过的手艺，这次没踩共享行的坑）。


def matmul(A, B):
    """嵌套列表矩阵乘法：(m,k) @ (k,n) -> (m,n)。"""
    rows_a, cols_a = len(A), len(A[0])
    rows_b, cols_b = len(B), len(B[0])
    if cols_a != rows_b:
        raise ValueError(f"形状不匹配：A 是 ({rows_a}, {cols_a})，B 是 ({rows_b}, {cols_b})，内维 {cols_a} != {rows_b}")
    C = [[0.0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        Ai = A[i]
        Ci = C[i]
        for k in range(cols_a):
            a = Ai[k]
            Bk = B[k]
            for j in range(cols_b):      # i-k-j 循环序：Bk 提一次，内层只做乘加
                Ci[j] += a * Bk[j]
    return C


if __name__ == "__main__":
    import random
    import time

    import numpy as np

    rng = random.Random(42)

    # 1) 非方阵对拍
    A = [[rng.uniform(-1, 1) for _ in range(3)] for _ in range(2)]
    B = [[rng.uniform(-1, 1) for _ in range(4)] for _ in range(3)]
    mine = np.array(matmul(A, B))
    ref = np.array(A) @ np.array(B)
    assert np.allclose(mine, ref, atol=1e-9), "非方阵对拍失败"
    print(f"对拍1（非方阵 (2,3)@(3,4)）通过，最大误差 {np.abs(mine - ref).max():.2e}")

    # 2) 形状检查报错演示
    try:
        matmul([[1, 2, 3]], [[1, 2, 3]])
    except ValueError as e:
        print(f"对拍2（形状检查）：正确拒绝，报错 -> {e}")

    # 3) 64x64 耗时对比（各 3 遍取平均）
    N = 64
    M1 = [[rng.uniform(-1, 1) for _ in range(N)] for _ in range(N)]
    M2 = [[rng.uniform(-1, 1) for _ in range(N)] for _ in range(N)]
    n1, n2 = np.array(M1), np.array(M2)

    t0 = time.perf_counter()
    for _ in range(3):
        matmul(M1, M2)
    mine_time = (time.perf_counter() - t0) / 3

    t0 = time.perf_counter()
    for _ in range(3):
        n1 @ n2
    np_time = (time.perf_counter() - t0) / 3

    assert np.allclose(np.array(matmul(M1, M2)), n1 @ n2, atol=1e-9), "64x64 对拍失败"
    print(f"对拍3（64x64）通过；手写 {mine_time * 1000:.1f} ms vs numpy {np_time * 1000:.3f} ms，慢约 {mine_time / np_time:.0f} 倍")
