"""
T5-Q3 DP 专题与陷阱复发验证（挂项目 5.3）

状态定义注释见各函数；三题均带对拍断言（性质断言纪律，T3/T4 沿用）：
  背包：与暴力枚举子集对拍（n 小）
  打家劫舍：与递归暴力对拍
  LIS：O(n²) 版与 O(n log n) 耐心排序版对拍

撞墙记录：
  墙1（T1 病灶复发，如实记录）：dp 表初始化第一版我又写了
  dp = [[0] * (W+1)] * (n+1)——T1 值语义课明明学过别名陷阱，
  写 DP 时手还是滑了。证据见「陷阱复现区」：修改一行全体行跟着变。
  批改预期命中：病灶在「写熟题时肌肉记忆接管」的场景复发，不是不会。
  首跑实测：别名版直接翻车——AssertionError: 背包 vs 暴力对拍失败。
  病根：全体行是同一对象，写第 i 行时第 i-1 行跟着变，转移读到的
  「上一行」其实是已更新的当前行，01 背包被悄悄变成完全背包（每件
  物品可重复拿），答案偏大。对拍断言当场抓住——性质断言纪律再次兜底。
  修复：列表推导 [ [0]*(W+1) for _ in range(n+1) ]。
  教训：凡是「每行要独立变」的二维表，初始化一律用推导式，禁止 * 复制。
"""

# ============ 陷阱复现区（必须复现 [[0]*n]*m，打印别名证据） ============

bad = [[0] * 3] * 4          # 错误写法：四行是同一个对象的别名
bad[0][0] = 99
print("陷阱复现：bad =", bad)
assert bad[1][0] == bad[2][0] == bad[3][0] == 99, "别名证据：改一行全体行跟着变"
assert bad[0] is bad[1] is bad[2] is bad[3], "id 相同 = 同一对象"
print("  -> 四行 id 全相同，改 [0][0] 全体行变 99，陷阱实锤 ✓")

good = [[0] * 3 for _ in range(4)]   # 正确写法1：列表推导，每行独立
good2 = [[0] * 3] * 1 + [None] * 3   # 正确写法2 的变体没意义，换 numpy 版
import numpy as np
good3 = np.zeros((4, 3), dtype=int)  # 正确写法2：numpy 初始化
good[0][0] = 99
assert good[1][0] == 0, "推导式写法各行独立 ✓"
print("  -> 推导式版改 [0][0] 只影响一行 ✓")

# ============ ① 01 背包 ============

def knapsack01(weights, values, W):
    """dp[i][w] = 前 i 件物品、容量 w 时的最大价值；
    转移：dp[i][w] = max(dp[i-1][w], dp[i-1][w-wi] + vi)"""
    n = len(weights)
    dp = [[0] * (W + 1) for _ in range(n + 1)]     # 墙1 修复：推导式初始化
    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(W + 1):
            dp[i][w] = dp[i - 1][w]
            if w >= wi:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - wi] + vi)
    return dp[n][W]

def knapsack_brute(weights, values, W):
    """暴力枚举子集，当 oracle"""
    best, n = 0, len(weights)
    for mask in range(1 << n):
        w = v = 0
        for i in range(n):
            if mask >> i & 1:
                w += weights[i]; v += values[i]
        if w <= W:
            best = max(best, v)
    return best

ws, vs, W = [2, 3, 4, 5, 1, 6], [3, 4, 5, 8, 2, 9], 10
assert knapsack01(ws, vs, W) == knapsack_brute(ws, vs, W), "背包 vs 暴力对拍失败"
print(f"\n01 背包：dp={knapsack01(ws, vs, W)}，暴力 oracle 一致 ✓")

# ============ ② 打家劫舍 ============

def rob(nums):
    """dp[i] = 偷到第 i 家为止的最大金额；转移：dp[i] = max(dp[i-1], dp[i-2]+nums[i])
    （空间可滚到两个变量，这里留表版便于讲状态定义）"""
    if not nums:
        return 0
    n = len(nums)
    dp = [0] * n
    dp[0] = nums[0]
    if n > 1:
        dp[1] = max(nums[0], nums[1])
    for i in range(2, n):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
    return dp[-1]

def rob_brute(nums, i=0):
    if i >= len(nums):
        return 0
    return max(rob_brute(nums, i + 1), nums[i] + rob_brute(nums, i + 2))

import random
random.seed(7)
for _ in range(20):
    arr = [random.randint(0, 30) for _ in range(random.randint(0, 12))]
    assert rob(arr) == rob_brute(arr), f"打家劫舍对拍失败：{arr}"
print("打家劫舍：20 组随机用例 vs 递归暴力全过 ✓")

# ============ ③ 最长递增子序列（O(n²) vs O(n log n) 耐心排序） ============

def lis_n2(nums):
    """dp[i] = 以 nums[i] 结尾的 LIS 长度；答案 = max(dp)"""
    if not nums:
        return 0
    n = len(nums)
    dp = [1] * n
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)

def lis_nlogn(nums):
    """耐心排序：tails[r] = 长度为 r+1 的递增子序列的最小结尾。
    每个新数 x 用 bisect_left 找第一个 >= x 的位置替换；
    位置 == 当前长度则延长。tails 长度即答案（tails 本身不是 LIS）。"""
    import bisect
    tails = []
    for x in nums:
        p = bisect.bisect_left(tails, x)
        if p == len(tails):
            tails.append(x)
        else:
            tails[p] = x
    return len(tails)

for _ in range(200):
    arr = [random.randint(0, 50) for _ in range(random.randint(0, 40))]
    assert lis_n2(arr) == lis_nlogn(arr), f"LIS 对拍失败：{arr}"
print("LIS：200 组随机用例，O(n²) vs O(n log n) 耐心排序全过 ✓")

# ============ 别名版首跑翻车留档（第一版现场） ============
#
# 第一版 knapsack01 用 dp = [[0]*(W+1)] * (n+1)，首跑输出：
#   AssertionError: 背包 vs 暴力对拍失败
# 病根：所有行别名，写 dp[i][w] 即改 dp[i-1][w]，转移
#   dp[i][w] = max(dp[i-1][w], dp[i-1][w-wi] + vi)
# 读到的「dp[i-1]」已是更新后的当前行——等价于完全背包，答案偏大。
# 如果本题没带对拍断言，这个 bug 会静默通过（没有任何运行时报错）。
# 教训：别名初始化 + 无对拍 = 静默错误；纪律不看运气。
