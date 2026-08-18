# T4-01 教练出题：PyTorch 基础（训练闭环）

> 教练 agent 出题稿（题干版，两分支共有）。评分要点、三级提示与参考答案见 `T4-01-教练密卷-PyTorch基础.md`（仅教练分支，学员禁阅）。
> 原料说明：本线为复习线；本轮从「跑过教程 notebook」升级到「每一步讲到机制」，考点按 [[01-学员人设卡.md|人设卡]] T4 预期漏洞逐条设计。
> 作答规则：闭卷硬推，卡住逐级要提示（弱→中→强），绝不直接要答案（C1/C2）；概念题与代码题分开判定（C3）。
> **复习线特别条款**：本轮重点盯「教程肌肉记忆 ≠ 机制理解」——训练循环五步每一步都要讲到「为什么有这一步、去掉会怎样」；沿用 T3 遗留观察项：① 推导链断环（反向传播链重点盯）② 性质断言兜底（梯度对拍必须带判据）。费曼稿必须含「给 iOS 同事讲懂」自检段落。

## 一、共识模型（教练版五个骨架）

学员先自推五模型再对本版，标注差异。

| # | 模型 | 一句话骨架 |
|---|------|-----------|
| M1 | Tensor = ndarray + 记账本 | 数值计算同 numpy，但 requires_grad 的张量每次运算都在计算图上记一条边；backward 沿图遍历，梯度是「遍历的结果」不是「某一步的结果」 |
| M2 | 动态图 define-by-run：图是现搭现拆的 | 每次 forward 现建计算图，backward 用完即拆——所以同一张图不能 backward 两次；「图」活在运行时的对象树里，不在代码文本里 |
| M3 | 梯度是累加不是覆盖 | `.grad` 语义是 ∂L/∂param 在本图上的贡献，多次 backward 累加——这是 feature（梯度累积、多 loss 相加），忘 zero_grad 就是事故 |
| M4 | nn.Module = 参数容器 + 行为协议 | 参数靠注册机制被 `parameters()` 收集（Parameter / 子模块自动递归）；`__call__` 包 forward 管 hook 与模式，直接调 forward 绕过协议 |
| M5 | 训练五步循环：forward → loss → zero_grad → backward → step | 每一步都有「去掉会怎样」的答案；DataLoader 把「喂 batch」独立成管道（Dataset 定义样本、DataLoader 定义批次） |

## 二、争议焦点（三题，考有边界的立场）

- **F1**：动态图（PyTorch）vs 静态图（早期 TensorFlow）——define-by-run 换来的调试友好，代价是什么？什么场景下静态图的优化（图级编译/裁剪）反而占优？给出边界。
- **F2**：view 共享存储 vs clone 拷贝——什么时候该用 view（省内存），什么时候必须 clone/detach？拿你熟悉的心智模型（提示：Swift CoW 在这里帮不了你）讲清分界线。
- **F3**：梯度累加是 bug 还是 feature？有人说 zero_grad 这个 API 本身就是设计失误，你站哪边？给出「累加被有意利用」的真实场景。

## 三、拷问题——概念口述通道（C1–C6）

**C1（M3）**：一个 batch 上连续调两次 `loss.backward()`（中间不 zero_grad），参数的 `.grad` 是什么？为什么 autograd 选择「累加」而不是「覆盖」——从「多次 backward 的合法用途」和「引擎无法知道你的意图」两个角度回答。

**C2（M4）**：nn.Module 三连——① 为什么训练时不能直接 `model.forward(x)`，要走 `model(x)`？`__call__` 里除了 forward 还管什么？② `parameters()` 是怎么把参数「收集」出来的——你赋一个普通 `torch.tensor` 给模块属性，会被收集吗？`nn.Parameter` 与普通 tensor 的差别是什么？③ 子模块的嵌套参数靠什么机制被递归收集？

**C3（M2）**：「拿函数调用链理解 autograd」错在哪——① backward 时梯度从哪走到哪、沿途做什么？② 计算图里的「节点」是什么（是函数？是变量？）？③ 为什么同一个 loss 第二次 backward 会报错——图在什么时候被销毁？

**C4（M1）**：`b = a.view(...)` 后改 b，a 变不变？反向呢——b 参与了带梯度的计算，梯度会不会「流回」a？为什么 Swift 的 CoW 直觉（改副本不影响原件）在这里完全不适用？再答：`detach()` 和 view 的差别是什么？

**C5（M2/M3）**：in-place 操作三连——① `x += 1`（x 参与过带梯度的图）为什么会出事？讲出版本号机制（version counter）的作用。② 为什么 `optimizer.step()` 里参数更新常用 in-place（如 `param.data.add_`）反而安全？③ 训练循环里 `loss.item()` vs 直接拿 loss 张量做统计，区别是什么？

**C6（M5）**：训练五步循环每一步的「去掉会怎样」——① 去掉 zero_grad；② 去掉 backward 直接 step；③ step 放在 backward 之前；④ 去掉 loss 直接用某个中间激活 backward。四问全答才计全过。

## 四、拷问题——代码任务通道（Q1–Q4）

代码要求：一律用 `.venv/bin/python` 跑通（torch 2.13.0 已装），输出贴回作答稿；文件落 `代码/T4/`，文件头注释标对应题号与撞墙记录。挂靠项目见 [[02-项目驱动实践路线.md|项目路线]] Phase 4。

**Q1（挂项目 4.1，M1/M2）**：**纯 Python/numpy 手推反向传播**。两层 MLP（D_in=4, H=8, D_out=2）+ softmax + 交叉熵，numpy 实现前向；**手写每一层的梯度公式**（W1/b1/W2/b2 全推），固定种子、固定输入，与「数值梯度」（中心差分 `(f(x+e)-f(x-e))/2e`，逐元素抽查至少 5 个位置）对拍，相对误差 < 1e-5。文件头写出 dL/dW2 与 dL/dW1 的推导链（链式法则每一环）。禁用 torch。

**Q2（挂项目 4.2，M1–M5）**：**torch 训练循环迁移**。把 Q1 的 MLP 用 `nn.Module` 重写（手写 Linear 层也行、nn.Linear 也行，但要讲清参数被收集的机制），写完整五步训练循环在同一批数据上训练 100 步；**与 Q1 的手写梯度做数值对拍**（同一初始化、同一输入，grad 对拍相对误差 < 1e-5），并打印 loss 下降曲线首尾值。对拍不过不许交。

**Q3（挂项目 4.3，M2/M3）**：**梯度诊断工具箱（最小复现集）**。四个独立小实验各配「翻车证据 + 修复版」：① 不 zero_grad 连续 backward 三次，打印 `.grad` 的数值爆炸轨迹；② in-place 操作破坏计算图复现 `RuntimeError`（贴完整报错）；③ view 共享存储下的梯度回流演示（b = a.view(...)，b 参与 loss，打印 a.grad 非空）；④ 梯度爆炸或消失一个（深网络/大学习率任选，打印梯度范数轨迹）。每个实验注释里写「机制一句话 + 修复纪律一句话」。

**Q4（挂项目 4.4，M5）**：**Dataset/DataLoader 管道**。自定义 Dataset 包裹 Q1/Q2 的数据（实现 `__len__`/`__getitem__`），写一个非平凡的 `collate_fn`（如按长度补齐 padding 或附加样本权重），DataLoader 配 shuffle 与 batch_size=8 训练 Q2 的模型至少 5 个 epoch；验证：① 同一 seed 下两遍数据顺序一致、不同 seed 不同；② 手动逐 batch 累加的平均 loss 与一遍全量前向的 loss 一致（对拍判据）；③ 讲清 Dataset 与 DataLoader 的职责分界。
