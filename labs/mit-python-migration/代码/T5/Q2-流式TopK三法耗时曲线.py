"""
T5-Q2 流式 Top-K 三法耗时曲线（挂项目 5.2）

撞墙记录：
  墙1（预期翻车，如实记录）：写这题前我押 bisect.insort 法「二分定位
  O(log n)，应该和堆差不多快」——刷题时二分给我的印象太深，忘了
  insort = bisect 定位 + list.insert，后者的搬移是 O(k)。实测 k=n/10、
  n=1e5 时 insort 法已经比堆法慢约一个数量级；n=1e6 的组合我直接
  不敢跑了（见下方 SKIP 说明）。教训：二分只帮你「找位置」，搬数据
  的成本要看容器。
  墙2（真实翻车）：insort 法第一版维护「升序原值列表」，写比较门槛时
  把方向搞反（拿 x 和 lst[0] 比导致留住的是 K 小），对拍抓出后
  改成维护「取负的升序列表」，门槛判断变成 lst[-1]，方向单一不拧巴。

SKIP 说明（诚实条款）：n=1e6 且 k=n/10=1e5 的组合，insort 法每次
真实插入是 O(k) 的 C 层搬移，预计插入次数约 k·ln(n/k)≈2e5 次，
总搬移量 ~2e10，本机预估分钟级以上——不跑，表里如实标注 SKIP。
"""
import time
import random
import heapq
import bisect


def topk_sort(data, k):
    return sorted(data, reverse=True)[:k]


def topk_heap(data, k):
    """最小堆，堆顶 = 当前 Top-K 的门槛（最弱者）"""
    h = []
    for x in data:
        if len(h) < k:
            heapq.heappush(h, x)
        elif x > h[0]:
            heapq.heapreplace(h, x)
    return sorted(h, reverse=True)


def topk_insort(data, k):
    """维护「取负后的升序列表」：前 k 个负值最小 = 原值最大的 k 个"""
    lst = []                          # 升序存 -x
    for x in data:
        nx = -x
        if len(lst) < k:
            bisect.insort(lst, nx)
        elif nx < lst[-1]:          # x 比当前门槛大才有资格
            bisect.insort(lst, nx)
            lst.pop()               # 踢掉最弱者
    return sorted((-v for v in lst), reverse=True)


# ---------- 对拍：三法结果一致 ----------
random.seed(3)
small = [random.random() for _ in range(5000)]
for k in (1, 7, 100):
    a = topk_sort(small, k)
    b = topk_heap(small, k)
    c = topk_insort(small, k)
    assert a == b == c, f"k={k} 三法结果不一致"
print("对拍：n=5000、k∈{1,7,100}，三法结果一致 ✓")


# ---------- 耗时曲线 ----------
def bench(fn, data, k):
    t0 = time.perf_counter()
    fn(data, k)
    return time.perf_counter() - t0


print(f"\n{'n':>8} {'k':>8} | {'排序法':>9} | {'heapq 法':>9} | {'insort 法':>10}")
for n in (10000, 100000, 1000000):
    random.seed(5)
    data = [random.random() for _ in range(n)]
    for k in (10, n // 10):
        t_s = bench(topk_sort, data, k)
        t_h = bench(topk_heap, data, k)
        if n >= 1000000 and k > 10:
            t_i = float("nan")       # SKIP：见文件头说明
            print(f"{n:>8} {k:>8} | {t_s:>8.3f}s | {t_h:>8.3f}s | {'SKIP':>10}")
        else:
            t_i = bench(topk_insort, data, k)
            print(f"{n:>8} {k:>8} | {t_s:>8.3f}s | {t_h:>8.3f}s | {t_i:>9.3f}s")

print("\n结论：k=10 时堆法近线性、insort 的搬移成本被小 k 掩盖；")
print("k=n/10 时 insort 的 O(k) 搬移显形（比堆法慢一个量级），排序法对 k 不敏感。")
print("复杂度定增长、常数定起点、k/n 比值决定三法胜负。")
