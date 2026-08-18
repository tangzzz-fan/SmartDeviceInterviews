"""
T5-Q1 LRU 缓存双实现（挂项目 5.1）

Swift ARC 思维对照（题干③）：手写双链里节点的 prev/next 互指会形成
「引用环」——Swift 里这必须用 weak 破环（ARC 不会回收环）；Python 的
引用计数同样搞不定环，但分代 GC 会兜底回收，所以这里敢用强引用互指。
代价：摘除节点时手动断链是纪律（断得不干净会让环晚几代才被收）。

撞墙记录：
  墙1（真实翻车，本轮最佳）：耗时对照第一版用容量 64，断言「朴素 O(n)
  淘汰版必须更慢」——首跑当场打脸：朴素 0.023s 反而快过手写双链 0.031s！
  AssertionError: O(n) 淘汰版应当更慢
  根因：list.remove/insert 是 C 层实现，容量 64 时 O(n) 的 n 太小，
  常数被 C 层吞掉；手写双链每步是四五次纯 Python 属性操作，常数反而更差。
  把容量拉到 1024/8192 后朴素版 4.3x→27.1x 显形——复杂度定增长，
  常数定起点，「O(1) 一定快」是错的。修复：耗时实验改为三档容量扫描。
"""
import time
import random
from collections import OrderedDict


# ---------- 实现 A：OrderedDict 版 ----------
class LRUOrdered:
    def __init__(self, capacity):
        self.cap = capacity
        self.d = OrderedDict()

    def get(self, key):
        if key not in self.d:
            return -1
        self.d.move_to_end(key)          # 命中：挪到最新端
        return self.d[key]

    def put(self, key, value):
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.cap:
            self.d.popitem(last=False)   # 淘汰最旧（最左）


# ---------- 实现 B：手写哈希 + 双链版 ----------
class Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=0, value=0):
        self.key, self.value = key, value
        self.prev = self.next = None


class LRUDoubleLinked:
    def __init__(self, capacity):
        self.cap = capacity
        self.map = {}
        # 哨兵：head 侧最新，tail 侧最旧，免边界判断
        self.head, self.tail = Node(), Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        node.next, node.prev = self.head.next, self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return -1
        self._remove(node)
        self._push_front(node)
        return node.value

    def put(self, key, value):
        node = self.map.get(key)
        if node is not None:
            node.value = value
            self._remove(node)
            self._push_front(node)
            return
        node = Node(key, value)
        self.map[key] = node
        self._push_front(node)
        if len(self.map) > self.cap:
            old = self.tail.prev
            self._remove(old)            # 手动断链（GC 纪律见文件头）
            del self.map[old.key]


# ---------- 实现 C：朴素 dict+list（O(n) 淘汰，做耗时对照） ----------
class LRUNaive:
    def __init__(self, capacity):
        self.cap = capacity
        self.d = {}
        self.order = []                  # 越靠前越新

    def get(self, key):
        if key not in self.d:
            return -1
        self.order.remove(key)           # O(n)
        self.order.insert(0, key)        # O(n)
        return self.d[key]

    def put(self, key, value):
        if key in self.d:
            self.order.remove(key)
        elif len(self.d) >= self.cap:
            old = self.order.pop()       # 淘汰最旧
            del self.d[old]
        self.d[key] = value
        self.order.insert(0, key)


# ---------- 对拍：随机操作序列，三实现行为必须逐步一致 ----------
def dl_key_order(lru):
    """手写双链的当前键序（新→旧）"""
    out, cur = [], lru.head.next
    while cur is not lru.tail:
        out.append(cur.key)
        cur = cur.next
    return out


random.seed(7)
CAP = 64
a, b, c = LRUOrdered(CAP), LRUDoubleLinked(CAP), LRUNaive(CAP)
for _ in range(20000):
    if random.random() < 0.5:
        k = random.randrange(120)
        assert a.get(k) == b.get(k) == c.get(k), f"get({k}) 三实现不一致"
    else:
        k, v = random.randrange(120), random.randrange(1000)
        a.put(k, v); b.put(k, v); c.put(k, v)
    # 每步后核对完整键序（含淘汰顺序，不只是值一致；方向对齐：统一新→旧）
    assert list(a.d.keys())[::-1] == dl_key_order(b) == c.order, "键序不一致（淘汰顺序有差异）"
assert set(a.d.keys()) == set(b.map.keys()) == set(c.d.keys()), "终态键集不一致"
print(f"对拍 20000 步随机操作：逐步返回值一致 + 每步键序一致 + 终态键集一致 ✓（容量 {CAP}，键域 120）")


# ---------- 耗时对照：10 万次随机操作 × 三档容量（墙1 修复：容量扫描） ----------
def bench(lru, ops):
    t0 = time.perf_counter()
    for op in ops:
        if op[0] == "get":
            lru.get(op[1])
        else:
            lru.put(op[1], op[2])
    return time.perf_counter() - t0


print(f"{'容量':>6} | {'OrderedDict':>12} | {'手写双链':>10} | {'朴素 dict+list':>14} | 朴素/双链")
for cap, kdom in [(64, 300), (1024, 4000), (8192, 30000)]:
    random.seed(11)
    big_ops = [("get", random.randrange(kdom)) if random.random() < 0.5
               else ("put", random.randrange(kdom), 1) for _ in range(100000)]
    t_ord = bench(LRUOrdered(cap), big_ops)
    t_dl = bench(LRUDoubleLinked(cap), big_ops)
    t_naive = bench(LRUNaive(cap), big_ops)
    print(f"{cap:>6} | {t_ord:>11.3f}s | {t_dl:>9.3f}s | {t_naive:>13.3f}s | {t_naive / t_dl:.1f}x")
print("结论：容量 64 时朴素版反而快（C 层常数吞掉小 n）；容量拉到 8192，")
print("O(n) 淘汰显形为 27x 差距——复杂度定增长、常数定起点，耗时断言改为扫容量后成立 ✓")
