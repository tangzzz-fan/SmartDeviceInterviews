# Q3（T3 挂项目 3.3）：softmax 数值稳定性实验——naive vs 减最大值 + log_softmax
# 撞墙记录：
#   墙1：第一版把「先 softmax 再 log」的坏写法对照配了稳定版 softmax_stable——
#        结果两行输出一模一样，「坏」根本没演示出来：减最大值后最大项恒为 exp(0)=1，
#        log(1)=0 永不下溢。坏写法的病要在 naive 版（不减最大值）+ 全大负数时才犯：
#        exp 集体下溢到 0，log(0) = -inf。改配对后真实复现。


import numpy as np


def softmax_naive(x):
    e = np.exp(x)
    return e / e.sum()


def softmax_stable(x):
    c = x.max()
    e = np.exp(x - c)
    return e / e.sum()


def log_softmax(x):
    c = x.max()
    return x - c - np.log(np.exp(x - c).sum())


if __name__ == "__main__":
    # ① float32 下触发溢出
    big = np.array([1.0, 50.0, 100.0], dtype=np.float32)
    print("logits =", big, "（float32）")
    with np.errstate(over="ignore", invalid="ignore"):
        naive_out = softmax_naive(big)
    print(f"naive 版输出：{naive_out}  <- exp(100) 在 float32 里爆了")
    stable_out = softmax_stable(big)
    print(f"稳定版输出：  {stable_out}")
    assert np.isfinite(stable_out).all(), "稳定版不该出现 inf/nan"

    # ② 正常范围内两版一致
    rng = np.random.default_rng(3)
    x = rng.uniform(-10, 10, size=100)
    assert np.allclose(softmax_naive(x), softmax_stable(x), atol=1e-12), "正常范围两版应一致"
    print("正常范围（-10~10）两版输出一致，误差 < 1e-12 ✓")

    # ③ log_softmax 与「先 softmax 再 log」对比（naive 版 + 全大负数才犯病）
    very_neg = np.array([-900.0, -901.0, -902.0], dtype=np.float64)
    print(f"\n全大负数 logits：{very_neg}")
    print(f"log_softmax 输出：                    {log_softmax(very_neg)}")
    with np.errstate(divide="ignore", invalid="ignore"):
        bad = np.log(softmax_naive(very_neg))
    print(f"先 naive softmax 再 log（坏写法）： {bad}")
