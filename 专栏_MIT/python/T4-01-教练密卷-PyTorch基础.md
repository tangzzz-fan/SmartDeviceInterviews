# T4-01 教练密卷：PyTorch 基础（仅教练分支，学员禁阅）

> 配套题干：`T4-01-教练出题-PyTorch基础.md`。本文件含判分点、弱/中/强三级提示、复习线变式题、失真自查清单。
> 复习线判定基准：**会跑但讲不出机制 = 半过**（本轮「教程肌肉记忆」等价于 T2/T3 的「会算无直觉」）；推导链断环按断环判；答得太顺 → 追加变式题降档。
> 人设卡对拍锚点（01-学员人设卡.md T4 节原文）：计算图心智缺失（拿函数调用链理解 autograd、答不出梯度为什么累加）；view 拿 Swift CoW 直觉；in-place 破坏计算图不知道；nn.Module 的 `__call__`/参数收集讲不清。首轮预期：C2/C3/C4 高发半过或未过。

## 一、概念题判分点与提示梯

### C1 两次 backward 与梯度累加
- **判分点**：① `.grad` 变成两倍（累加不覆盖）；② 累加是 feature 的两类真实用途：梯度累积（显存不够时多个 micro-batch 的 backward 攒够再一次 step，等价大 batch）、多任务多 loss（loss1.backward(); loss2.backward(); step）；③ 引擎视角：autograd 无法知道「这是不是最后一次 backward」，覆盖语义会悄悄破坏上面两类合法用法，累加是线性安全的默认（微分本身是线性的：∂(L1+L2) = ∂L1+∂L2）。只答「会变大」不答用途 = 半过。
- **弱提示**：想想显存装不下大 batch 时大家怎么训？
- **中提示**：两个 loss 加权求和的训练（多任务学习）里，backward 分别调还是合起来调？
- **强提示**：autograd 不知道你调几次 backward——如果它默认覆盖，第二次调会把第一次的梯度弄丢。
- **复习线变式**：梯度累积为什么在数学上等价于大 batch？（loss 取平均时，N 个 micro-batch 的平均梯度 = 全 batch 平均梯度，线性性。）

### C2 nn.Module 三连
- **判分点**：① `model(x)` 走 `__call__`，它负责跑 forward hooks / backward hooks（register_forward_hook 等）并统一入口；直接 `model.forward(x)` 绕过 hook——训练能跑但监控/调试/特征提取工具全失效；② 普通 `torch.tensor` 赋给模块属性**不会**被收集（只是普通 Python 属性）；`nn.Parameter` 是 Tensor 子类、默认 requires_grad=True，且 Module 的 `__setattr__` 会拦截它注册进 `_parameters` 字典；③ 子模块同样被 `__setattr__` 注册进 `_modules`，`parameters()` 递归遍历 `_modules` + `_parameters` 收集。讲到「__setattr__ 拦截注册」= 过；只说「Parameter 会被收集」= 半过；说不清注册机制 = 未过。
- **弱提示**：Module 重写了哪个 Python 魔术方法来「拦截赋值」？
- **中提示**：print 一下 `model._parameters` 和 `model._modules`。
- **强提示**：`__setattr__` 里判断值是不是 nn.Parameter / nn.Module，是就塞进内部字典；parameters() 递归这两个字典。
- **复习线变式**：`register_buffer`（如 BatchNorm 的 running_mean）为什么不是 Parameter？（参与 forward 但不需要梯度、不进优化器，要随 state_dict 保存。）

### C3 计算图不是函数调用链
- **判分点**：① backward 从 loss 节点出发沿图**逆拓扑序**遍历，每个节点用保存的中间量算局部导数，与上游传来的梯度做链式相乘，叶节点（requires_grad）累加进 `.grad`；② 节点是**张量**（非叶张量挂 grad_fn 记录产生它的运算），不是函数——函数执行完就没了，图是运行时对象；③ 第一次 backward 默认释放非叶节点的缓冲区（retain_graph=False），第二次 backward 报 `Trying to backward through the graph a second time... specify retain_graph=True`。拿「函数返回栈」讲的 = 未过（正中人设漏洞）。
- **弱提示**：函数早就返回了，backward 的时候中间值从哪来？
- **中提示**：打印 `loss.grad_fn` 和 `h.grad_fn` 看看链。
- **强提示**：每个参与运算的输出张量都挂一个 grad_fn 节点，backward 是这张 DAG 上的遍历。
- **复习线变式**：`retain_graph=True` 什么时候必须用？（同一张图要 backward 多次，如 GAN 判别器/生成器共享前向、多 loss 分开反传。）

### C4 view 共享存储与梯度回流
- **判分点**：① view 与原张量**共享底层存储**，改 b 即改 a（立即生效，没有拷贝）；② 梯度会流回：view 是图上的一个节点，b 的梯度经 view 节点（必要时 reshape 回去）累加进 a.grad；③ CoW 错在哪：Swift CoW 是「写时复制」——写操作触发拷贝，改副本不动原件；torch view 是**共享引用无拷贝**，写直接穿透；④ detach() 返回新张量：共享存储但**切断图连接**（grad_fn 置空、requires_grad=False）——view 保图、detach 断图，两个正交维度。只答「view 是浅拷贝」= 半过。
- **弱提示**：b = a.view(...) 之后 `b.data_ptr() == a.data_ptr()` 吗？
- **中提示**：CoW 的「写」触发什么动作？torch 的 view 写的时候有这个动作吗？
- **强提示**：view 共享存储且留在图里；detach 共享存储但脱离图；clone 拷贝存储留在图里。
- **复习线变式**：`b = a.reshape(...)` 一定共享存储吗？（不一定——内存连续时是 view，不连续时内部先 copy，返回独立存储。）

### C5 in-place 三连
- **判分点**：① 每个张量有 version counter，每次 in-place 修改自增；backward 需要用到前向时保存的张量，发现版本号对不上就抛 RuntimeError（防止用被污染的数算出错误梯度——宁可炸不装对）；② optimizer.step 里对**叶参数**做 in-place 是安全的：backward 已完成、图已释放，更新只发生在图外；且走 `param.data`/`detach()` 绕过版本追踪；③ loss.item() 取出 Python 标量、切断图引用；直接存 loss 张量做统计会让计算图无法释放，显存随步数泄漏。只答「in-place 会报错」不讲版本号 = 半过。
- **弱提示**：autograd 怎么知道「保存下来的张量被改过」？
- **中提示**：报错信息里有 version 字样——expected version 0, got version 1。
- **强提示**：version counter 在前向保存张量时记下版本，backward 时对不上就炸。
- **复习线变式**：`torch.Tensor.add`（非 in-place）为什么没这个问题？（产生新张量、新节点，旧保存量不受影响。）

### C6 五步循环的「去掉会怎样」
- **判分点**：① 去掉 zero_grad：梯度跨步累加，等效学习率随步数线性膨胀 → 震荡/发散；② 去掉 backward 直接 step：首次 grad 为 None 直接报错，之后拿**上一步的陈旧梯度**更新，方向与当前 loss 无关；③ step 在 backward 前：用陈旧梯度（滞后一步），首步 None 报错；④ 用中间激活 backward：优化的是「让激活变大」而不是任务损失，梯度方向被篡改（除非那正是你要的正则项）。四问全对 = 过；缺一问按断链判。
- **弱提示**：每一步都在修谁的数值——grad 还是 param？
- **中提示**：grad 是「本步 loss 对参数的贡献」，不清零会怎样？
- **强提示**：把五步写成时序：算 grad（backward）→ 清零（zero_grad）→ 用 grad 改 param（step）。
- **复习线变式**：推理代码里为什么三步都不要（no_grad + eval）？（不建图省显存、关 dropout/BN 训练态。）

## 二、争议焦点判分点

- **F1 动静图**：动态图代价——每次前向重新建图有开销、图级优化（算子融合、内存规划、自动并行）做不了；静态图占优场景——部署端固定形状的推理、超大模型编译优化（注：torch.compile 本质就是把动态图 trace 成静态图再优化，两条路线在收敛）。有「torch.compile/部署编译」这层 = 过。
- **F2 view vs clone**：view 省内存零拷贝，适合只读/形状变换；必须 clone/detach 的场景——要独立写入、要把张量带出图的生命周期（存日志/返回给用户）、防止梯度意外回流。分界线不是性能是**所有权**（像 Swift 里「这个 buffer 归谁管」）。
- **F3 累加 bug 或 feature**：feature 站得住——梯度累积、多 loss、MAML 类算法都依赖它；说 API 失误的合理内核是「默认值选择」之争（可以在 step 后自动清零，但会把「攒梯度」变复杂）。两面都碰且有真实场景 = 过。

## 三、代码题判分点

- **Q1**：推导链必须出现在文件头：p=softmax(z), L=−mean log p_y → ∂L/∂z=(p−onehot)/N → dW2=hᵀdz, db2=Σdz, dh=dz·W2ᵀ → ReLU 门 dh_pre=dh·(h>0) → dW1=Xᵀdh_pre, db1=Σdh_pre。中心差分对拍相对误差 `|a−b|/max(1,|a|,|b|)` < 1e-5 至少 5 个位置。断点预判：ReLU 处忘记乘门（h>0）、mean 的 1/N 漏掉、W2ᵀ 转置方向错——数值对拍会当场抓。
- **Q2**：初始化必须与 Q1 完全一致（`with torch.no_grad(): linear.weight.copy_(W1_T)` 注意 **nn.Linear 存的是转置**：y = xWᵀ+b，这是高发对拍失败点）；五步循环顺序正确；grad 对拍与 Q1 相对误差 < 1e-5。用 `model.forward(x)` 而非 `model(x)` 不算挂但追问 C2。
- **Q3**：四实验都要真实报错/数值证据。① grad 轨迹应为 1×→2×→3×；② 完整报错含 `modified by an inplace operation... version`；③ a.grad 非空且数值正确；④ 梯度范数随层深/步数单调爆炸或消失。每个实验的「机制一句话」必须点到版本号/共享存储/累加语义。
- **Q4**：collate_fn 必须真的做事（padding 或加权）；seed 判据两同两异；batch 平均 loss 与全量 loss 对拍（注意 DataLoader 最后一个 batch 可能不满，取整除或 drop_last 才严格一致）；职责分界：Dataset 管「第 i 个样本是什么」，DataLoader 管「怎么把样本组成 batch、以什么顺序、几路并行」。

## 四、失真自查清单（阅卷时跑）

1. 代码输出里的数值是否与代码文件实际运行结果一致（抽跑一个验证）。
2. 撞墙记录是否有真实报错文本（编造的墙通常没有 traceback 细节）。
3. 自评档位与判定是否大面积背离（自评全有把握但判定全半过 = 失真信号）。
4. Q2 对拍是否真做（贴了相对误差数值的才算）。
5. 密卷隔离：`git ls-tree -r --name-only feat/mit-python-study-student | grep 密卷` 应为空（注意 Swift 线公开归档文件按路径甄别）。
