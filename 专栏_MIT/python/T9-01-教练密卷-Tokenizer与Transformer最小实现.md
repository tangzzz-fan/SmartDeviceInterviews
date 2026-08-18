# T9-01 教练密卷：Tokenizer 与 Transformer 最小实现（仅教练分支，学员禁阅）

> 本文件含弱/中/强三级提示、评分要点与参考答案。使用纪律：直接要答案 → 反问「这一步的矩阵形状是什么」。

## 一、概念题：提示梯与评分要点

### C1 BPE 直觉与 token 成本
- 弱提示：BPE 从「字符」开始，每次合并什么（相邻对中最高频的）？
- 中提示：`low` 为什么先合并 `lo`？因为语料里 `lo` 比 `ow` 更常出现？token 数与 API 计费什么关系？
- 强提示：BPE = 贪心合并最高频相邻子词；token 数 = 计费单位与上下文窗口单位；中文每字约 1-2 token，英文约 0.75 token/词。
- 评分要点：真懂特征：合并直觉 + 计费/窗口意义 + 中英文差异。
- 参考答案：BPE 迭代合并最高频相邻对；token 是计费与窗口的度量；预算管理是 prompt 工程第一约束。

### C2 QKV 与缩放点积
- 弱提示：Q 问「我要找什么」，K 说「我是什么」，V 给「实际内容」——三种投影的意义？
- 中提示：点积大 = 方向接近；维度大时点积方差大 → softmax 饱和 → 为什么除 sqrt(d_k)？
- 强提示：Q/K/V 是三种线性投影；缩放除 sqrt(d_k) 保持 softmax 输入方差稳定；注意力 = softmax(QK^T/sqrt(d_k))V。
- 评分要点：真懂特征：三种投影语义 + 缩放动机。
- 参考答案：Q 查询、K 键、V 值；缩放稳定 softmax；注意力是相关性加权的值求和。

### C3 两种 mask
- 弱提示：因果 mask 防什么（未来泄漏）？填充 mask 防什么（padding 参与加权）？
- 中提示：mask 加在 softmax 之前（把非法位置设为 -inf）还是之后？
- 强提示：因果：上三角 -inf（softmax 前）；填充：padding 位置 -inf。位置很关键：softmax 后置 0 会把概率质量重新归一，等价但实现易错；前置 -inf 更标准。
- 评分要点：真懂特征：两种 mask 目的 + 正确位置（softmax 前 -inf）。
- 参考答案：因果防未来、填充防 padding；都在 softmax 前用 -inf（或等价大负数）。

### C4 残差与层归一化
- 弱提示：深层网络训练难，残差给梯度什么「捷径」？
- 中提示：层归一化在哪个维度归一（特征维，不是样本维）？为什么对 batch 不敏感？
- 强提示：残差 = 恒等捷径，缓解梯度消失与退化；LayerNorm 按特征维归一，不受 batch 影响（区别于 BatchNorm）；位置在子层之后、残差之前。
- 评分要点：真懂特征：残差动机 + LayerNorm 归一维度与位置。
- 参考答案：残差给梯度短路；LayerNorm 按特征维、在子层后残差前；是训练稳定性的工程件。

### C5 token 估算与窗口管理
- 弱提示：英文一个词大约几个 token？中文一个字呢？
- 中提示：窗口满了的策略有哪几种（截断 / 摘要 / 分块）？各自丢什么？
- 强提示：估算 ≈ 英文 0.75 token/词、中文 1-2 token/字（按 tokenizer 实测为准）；预算 = 窗口 - 输出预留；截断丢旧、摘要丢细节、分块丢全局。
- 评分要点：真懂特征：估算 + 预算公式 + 三策略取舍。
- 参考答案：用 tokenizer 实测为准；预算 = 窗口 - 输出预留；按场景选截断/摘要/分块。

### C6 生态工作流与互补
- 弱提示：HuggingFace 最小三步是什么（加载 tokenizer / 加载 model / generate）？
- 中提示：从零实现教会你「形状与数据流」，库教会你「规模与工程」——各缺什么？
- 强提示：工作流：`AutoTokenizer.from_pretrained` → `AutoModelForCausalLM.from_pretrained` → `model.generate`；从零实现给机制直觉，库给正确性/规模/工程。
- 评分要点：真懂特征：三步工作流 + 互补关系。
- 参考答案：tokenizer + model + generate 三步；从零实现建立机制心智，生态解决规模与工程。

## 二、争议焦点参考立场

- F1：从零实现到「形状与数据流」通、库到「规模与工程」通；只会库 = 半过，只从零 = 低效。
- F2：BPE 通用；WordPiece 是 BERT 家族变体；SentencePiece 处理多语言/无空格语言；按生态选。
- F3：公式 + 实现 + 直觉三层都要；只有公式 = 半过。

## 三、代码题：评分要点与提示

### Q1 BPE 最小实现
- 评分要点：训练（统计相邻对 + 合并）循环正确；encode/decode 往返一致；vocab/合并序列可打印。
- 参考答案要点：初始字符表；循环统计 `Counter(zip(tokens, tokens[1:]))` 取最高频合并；用 merges 表做编码。

### Q2 自注意力（numpy）
- 评分要点：单头 + 多头（2 头）形状正确；缩放点积 + softmax；三种 mask 打印注意力矩阵证明生效；mask 位置正确（softmax 前）。
- 参考答案要点：`attn = softmax(Q@K.T/sqrt(d_k) + mask)`；mask 用 -1e9；多头按头拆分再拼接。

### Q3 单层因果 Transformer
- 评分要点：embedding + 位置编码 + 自注意力 + FFN + 残差 + LayerNorm + 输出投影形状正确；因果性验证（改 i+1 输入不影响 i 的 logits）。
- 参考答案要点：位置编码用正弦或可学习表；因果 mask；残差 `x = x + attn(x)`；验证：固定 i 的 logits 对后位输入不敏感。

### Q4 HuggingFace 实操
- 评分要点：加载 → 编码 → 推理/生成 → 解码全流程；API 对照表含参数含义；离线则如实标「待验证」。
- 参考答案要点：`AutoTokenizer.from_pretrained("gpt2")`；`tokenizer(text, return_tensors="pt")`；`model.generate(**inputs)`；`tokenizer.decode(output[0])`。

## 四、使用纪律

- 判分只认证据：形状、mask 矩阵、往返一致性、因果性验证都要打印留档；「应该是对的」不算。
- 失真自查：mask 位置错、形状对不上、HuggingFace 没跑却写跑通 = 该题作废重跑。
