# T1 Q1 引用语义翻车合集（挂项目 1.4）
# 撞墙记录：
#   墙1：我一开始以为 a.copy() 之后的 b 和 a 完全隔离，跑完现场二才看清内层共享。
#   墙2：修复现场三时先写了 d2 = d（还是同一对象），id 对比打脸后改 deepcopy。
#   墙3：dict(d) 只隔一层这个点，是靠现场三变体实验撞出来的（见文件末尾）。

import copy

print("=== 现场一：可变默认参数累积 ===")

def tag_buggy(word, items=[]):
    items.append(word)
    return items

print("第一次:", tag_buggy("x"))   # 期望 ['x']
print("第二次:", tag_buggy("y"))   # 翻车：['x', 'y']，默认列表记住了上次
print("id 证据:", id(tag_buggy.__defaults__[0]))

def tag_fixed(word, items=None):
    if items is None:
        items = []
    items.append(word)
    return items

print("修复后第一次:", tag_fixed("x"))
print("修复后第二次:", tag_fixed("y"))  # 各自独立

print("\n=== 现场二：浅拷贝矩阵整列联动 ===")

m_bad = [[0] * 3] * 3
m_bad[0][0] = 99
print("翻车矩阵:", m_bad)  # 三行第一列全变 99
print("三行 id:", [id(row) for row in m_bad])  # 三个 id 相同

m_good = [[0] * 3 for _ in range(3)]
m_good[0][0] = 99
print("修复矩阵:", m_good)  # 只有第一行变
print("三行 id:", [id(row) for row in m_good])  # 三个 id 不同

print("\n=== 现场三：函数内改 dict 影响调用方 ===")

def mutate_buggy(d):
    d["leaked"] = True

caller_dict = {"name": "ios-dev"}
mutate_buggy(caller_dict)
print("翻车：调用方的 dict =", caller_dict)  # 被函数偷偷改了

def mutate_fixed(d, store):
    local = copy.deepcopy(d)
    local["leaked"] = True
    store.append(local)

caller_dict2 = {"name": "ios-dev"}
results = []
mutate_fixed(caller_dict2, results)
print("修复：调用方的 dict =", caller_dict2)  # 原样
print("修复：函数内部改的是 =", results[0])

print("\n=== 汇总断言 ===")
assert tag_fixed("a") == ["a"] and tag_fixed("b") == ["b"], "默认参数修复失败"
assert m_good[1][0] == 0 and m_good[2][0] == 0, "矩阵修复失败"
assert "leaked" not in caller_dict2, "dict 隔离修复失败"
print("三个修复全部隔离成功 ✔")

print("\n=== 附加撞墙：dict(d) 只隔一层 ===")
nested = {"k": [1, 2]}
shallow = dict(nested)
shallow["k"].append(3)
print("浅拷贝版 nested 也被改:", nested)  # dict(d) 挡不住嵌套可变对象
deep = copy.deepcopy(nested)
deep["k"].append(4)
print("deepcopy 版 nested 不受影响:", nested)
