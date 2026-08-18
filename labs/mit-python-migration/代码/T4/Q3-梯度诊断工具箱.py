"""
T4-Q3 梯度诊断工具箱：最小复现集（挂项目 4.3）

撞墙记录：
  墙1（预期翻车，如实记录）：实验②我第一版拿「叶参数上做 in-place」复现——
  w = nn.Parameter(...); w.data.add_(1)——跑了半天不报错。人设卡说得没错：
  我原本不知道 in-place 到底在哪种场景破坏计算图。两次试错（叶上 in-place
  不报、backward 之前 in-place 也不报，见墙3）后才明白：报错的触发条件是
  「图已建好、保存的中间量被就地改掉、还要再走一次反向」——版本号对不上
  才炸。最终复现写法见实验②。
  墙2（预期翻车）：实验①我原本赌「第二次 backward 会覆盖第一次的梯度」
  （函数调用心智的残留——每次调用返回新结果），实测是累加：3→6→9。
  墙3（真实翻车）：实验②第一版复现写法是 y = x * 2; y.add_(1); y.sum().backward()
  ——竟然不报错！根因没搞对：报错的触发条件是「先 backward 建好图（保存了
  中间量 y 的 version 0），再 in-place 把 y 改成 version 1，然后第二次 backward」；
  我第一版在 backward 之前就 add_ 完了，后续运算看到的是新值，没有版本矛盾。
  改成 backward 之后再 add_ + retain_graph 二次 backward，结果还是不报！
  墙4（真实翻车）：继续排查才发现，z = y.sum() 的反向根本不需要 y 的数值
  （sum 只记形状），所以改 y 不触发版本检查——得让下游运算真的「保存了 y」，
  改成 z = (y**2).sum()（pow 反向需要底数 y）才真实复现 RuntimeError。
  教训：「哪个 op 保存了哪个张量」决定了炸点在哪，报错信息里的
  「output 0 of Add/Mul/Pow」就是线索。

每个实验：机制一句话 + 修复纪律一句话，见各节注释。
"""
import torch
import torch.nn as nn

print("=" * 60)
print("实验① 不 zero_grad 的梯度累加")
# 机制：.grad 语义是累加，backward 只负责「把本图贡献加上去」，不清场。
# 纪律：训练循环 backward 前必 zero_grad；想攒梯度时把 zero_grad 挪到 step 后。
w = nn.Parameter(torch.tensor([1.0, 2.0]))
for i in range(3):
    loss = (w * 3.0).sum()          # ∂loss/∂w = [3,3]
    loss.backward()
    print(f"第 {i + 1} 次 backward 后 w.grad = {w.grad.tolist()}（应为 {3.0 * (i + 1)} 倍基值）")
assert w.grad.tolist() == [9.0, 9.0], "累加轨迹不对"
print("轨迹 3→6→9 ✓（预期覆盖的人设被实测纠正）")

print("=" * 60)
print("实验② in-place 破坏计算图")
# 机制：前向时 autograd 保存中间张量并记下 version；backward 发现版本对不上
# 就抛错——宁可炸也不拿被污染的数算错梯度。
# 纪律：带梯度的中间张量用 out-of-place 运算（y = x + 1 而非 x += 1）。

# 第一版（墙1）：叶参数上 in-place，图外操作，安然无恙——说明炸点不在叶上
w_leaf = nn.Parameter(torch.tensor([1.0]))
w_leaf.data.add_(1.0)
print(f"第一版：叶参数 data.add_ 不报错（值 = {w_leaf.item()}）——炸点在中间张量，不在叶")

# 第二版（墙3）：backward 之前 in-place——也不报错，后续运算看到的是新值
x0 = torch.tensor([1.0, 2.0], requires_grad=True)
y0 = x0 * 2.0
y0.add_(1.0)
(y0.sum()).backward()
print(f"第二版：backward 之前 add_，无版本矛盾，照常反传（x0.grad = {x0.grad.tolist()}）")

# 复现版：backward 建图（pow 保存了 y 的 version 0）→ in-place（version 1）→ 二次 backward
x = torch.tensor([1.0, 2.0], requires_grad=True)
y = x * 2.0
z = (y ** 2).sum()                     # 墙4：用 pow 而非 sum——pow 反向才保存 y
z.backward(retain_graph=True)          # 第一次反传：此时 y 记为 version 0
y.add_(1.0)                            # 就地改：y 变 version 1
try:
    z.backward()                       # 第二次反传：对不上版本号
    print("竟然没报错？检查复现条件")
except RuntimeError as e:
    print("复现成功，完整报错：")
    print(f"  RuntimeError: {e}")

print("=" * 60)
print("实验③ view 共享存储与梯度回流")
# 机制：view 与原张量共享底层存储、且在图上是连通节点，梯度经 view 流回原张量。
# 纪律：要切断梯度用 detach()，要独立存储用 clone()；view 只是换个形状看同一块内存。
a = torch.tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
b = a.view(-1)
print(f"共享存储证据：b.data_ptr() == a.data_ptr() → {b.data_ptr() == a.data_ptr()}")
loss = (b ** 2).sum()
loss.backward()
print(f"a.grad = {a.grad.tolist()}（应等于 2a）")
assert a.grad is not None and torch.allclose(a.grad, 2 * a.detach()), "梯度没回流"
print("梯度回流 ✓（Swift CoW『改副本不动原件』在这里完全不适用：无拷贝、写穿透）")

print("=" * 60)
print("实验④ 梯度爆炸：同一变换重复施加，梯度随深度指数增长")
# 机制：每层回传乘 Wᵀ；W = 1.5I 时 loss ∝ 1.5^(2d) = 2.25^d，梯度同阶放大——
# 深度每 +2，梯度 ×2.25² = ×5.0625，指数爆炸。
# 纪律：盯梯度范数随深度的轨迹（而不是各层之间的绝对值）；残差/归一化/裁剪是护栏。
W = torch.eye(8) * 1.5
x = torch.ones(1, 8, requires_grad=True)
print("深度 → ‖∂loss/∂x‖：")
prev = None
for depth in (2, 4, 6, 8, 10):
    y = x
    for _ in range(depth):
        y = y @ W
    loss = (y ** 2).sum()
    loss.backward()
    g = x.grad.norm().item()
    if prev:
        ratio = g / prev
        print(f"  深度 {depth:2d}: {g:.4e}（较上一档 ×{ratio:.2f}）")
        assert abs(ratio - 2.25 ** 2) < 0.1, f"放大比 {ratio:.2f} 不符理论值 5.06"
    else:
        print(f"  深度 {depth:2d}: {g:.4e}")
    x.grad = None
    prev = g
print("深度每 +2，梯度 ×5.06（=2.25² = 1.5⁴），指数爆炸实锤 ✓")
print("=" * 60)
print("四个实验全部复现完成 ✓")
