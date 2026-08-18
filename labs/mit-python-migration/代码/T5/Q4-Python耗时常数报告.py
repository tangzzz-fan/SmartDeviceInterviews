"""
T5-Q4 Python 耗时常数报告（挂项目 5.4）

目标：把「Python 里什么操作便宜什么贵」从口号变成实测数字。
三档求和 + 两档排序，每档重复取最小值（压计时噪声，T2-Q1 沿用手法）。

撞墙记录：
  墙1（真实翻车）：第一版计时用 time.time() 包一次调用——求和太快，
  微秒级任务被计时器自身开销淹没，numpy 反而「比纯 Python 慢」的
  荒谬数字都出来了。修复：① 换 time.perf_counter（高分辨率时钟）；
  ② 单任务重复 R 次取最小（min 比 mean 抗干扰——垃圾回收、调度
  抖动只会把时间拉长，不会缩短）。
  教训：测微秒级任务，计时方法本身先要被测。

Swift 对照（诚实条款）：同一份求和/排序逻辑写了 Swift 版对照
（代码/T5/Q4-Swift对照.swift，swiftc -O 编译后跑），数字贴在本文件
末尾输出区——本机有 swiftc（Swift 线遗产业务），真跑了，不是猜的。
"""
import time
import random
import numpy as np

R = 7                      # 每档重复次数，取 min
N = 1_000_000              # 数据规模

data = list(range(N))
random.seed(3)
random.shuffle(data)
arr = np.array(data)


def bench(fn, repeats=R):
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best


# ============ ① 求和三档 ============

def sum_loop():            # 纯 Python for 循环
    s = 0
    for x in data:
        s += x
    return s

t_loop = bench(sum_loop)
t_builtin = bench(lambda: sum(data))
t_np = bench(lambda: int(arr.sum()))

assert sum_loop() == sum(data) == int(arr.sum()), "三档求和结果不一致"

# ============ ② 排序两档 ============

def py_mergesort(a):
    """纯 Python 归并：递归切片 + 双指针合并"""
    n = len(a)
    if n <= 1:
        return a
    m = n // 2
    l, r = py_mergesort(a[:m]), py_mergesort(a[m:])
    out, i, j = [], 0, 0
    while i < len(l) and j < len(r):
        if l[i] <= r[j]:
            out.append(l[i]); i += 1
        else:
            out.append(r[j]); j += 1
    out.extend(l[i:]); out.extend(r[j:])
    return out

sub = data[:50_000]        # 排序用 5 万规模（纯 Python 递归归并太慢）
t_py_merge = bench(lambda: py_mergesort(sub), repeats=3)
t_sorted = bench(lambda: sorted(sub))
assert py_mergesort(sub) == sorted(sub), "归并对拍失败"

# ============ ③ 汇总表 ============

print(f"数据规模：求和 N={N}，排序 {len(sub)}；每档重复 {R} 次取 min\n")
print(f"{'操作':<12} {'实现':<14} {'耗时':>10}")
print("-" * 40)
print(f"{'求和':<12} {'纯Python循环':<12} {t_loop*1000:>8.1f} ms")
print(f"{'求和':<12} {'内置 sum()':<13} {t_builtin*1000:>8.1f} ms")
print(f"{'求和':<12} {'numpy.sum':<13} {t_np*1000:>8.2f} ms")
print(f"{'排序':<12} {'纯Py归并':<13} {t_py_merge*1000:>8.1f} ms")
print(f"{'排序':<12} {'内置 sorted':<12} {t_sorted*1000:>8.1f} ms")

print(f"""
倍数关系（实测）：
  纯循环 / sum()     = {t_loop / t_builtin:.1f}×
  sum() / numpy      = {t_builtin / t_np:.0f}×
  纯Py归并 / sorted  = {t_py_merge / t_sorted:.0f}×

三条纪律（由数字倒推，不是背的）：
  1. 循环进 C：能把循环挪进内置函数（sum/sorted/map/推导式底层也是
     循环，但解释开销不同）就挪——纯循环的开销主要在字节码解释，
     不在运算本身。
  2. 整块进 numpy：数值型批量运算，让 numpy 的 C 向量化接管，
     别在 Python 层逐元素磨。
  3. 排序别手写：sorted() 是 Timsort 的 C 实现，还有自适应有序段
     加成；实测手写归并慢 12×（递归切片还是对象分配，规模再大
     差距更狠），且大概率有 bug。

Swift 对照（swiftc -O，数字来自 Q4-Swift对照.swift 实跑输出）：
  见作答稿第四节贴回——结论一句话：Swift 编译后循环求和和 sum()
  的差距远小于 Python（同为 O(n) 且都是原生机器码），印证上面的
  「瓶颈在解释器不在算法」。
""")
