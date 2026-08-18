# T6-04 费曼草稿：async 与企业落地

> 学员写回稿。规则：不看任何资料重推五模型，写「给外行讲懂」的版本；按题干条款③，必含「TaskGroup vs Swift 结构化并发逐项对照表」与「给 iOS 同事讲懂」自检段落。

## 一、五模型重推（脱稿版）

**M1 协程是对象，不是动作**：`async def f()` 定义的「异步函数」被调用时一行代码都不跑，只返回一个 coroutine 对象——它是一张待执行的说明书，await 或 create_task 才是按下执行键。最危险的推论：**漏写 await 不报错**——对象被造出来又被丢弃，功能静默缺失，只有 GC 时来一行 RuntimeWarning。Swift 里编译器拦的事，Python 这里没人拦，所以「写 async 代码 = 先假设自己会漏 await」，靠测试兜底。

**M2 事件循环是一根线程上的协作调度**：asyncio 全程一根线程，协程靠主动 await 让出控制权，调度器只在让出点切换。「阻塞杀 loop」的严重性从这里推出来：time.sleep 没有让出点 = 调度器永远等不到切换 = **所有协程一起停摆**，不是只卡自己。我实测的崩塌表是铁证：16 个 0.1s 任务，asyncio.sleep 版 16 路并发 0.101s，time.sleep 版并发度从 1 加到 16 耗时 1.65s 一分不降。GCD 心智在这里失效——GCD 队列背后是线程池，asyncio 协程层没有「另一根队列」，阻塞活只能 run_in_executor 显式丢线程池（IO 阻塞值得丢，GIL 在等待时释放；CPU 密集丢线程池没用，得上 multiprocessing）。

**M3 结构化并发三件套**：TaskGroup（作用域出口等全部子任务、失败取消兄弟、ExceptionGroup 全量聚合）、asyncio.timeout（到期取消，CancelledError 在下一个 await 点抛出——取消是异步送达不是断电，所以 finally 有机会跑）、Semaphore（计数器闸门，限「同时在场数」不是速率，速率要令牌桶）。组合拳：入场限并发 + 指数退避带抖动（防重试风暴同步化）+ 退避上限与总预算。

**M4 流式消费 = 每步都能让出的迭代**：async for 背后 `__aiter__`/`__anext__`，每次 anext 是挂起点——这是与同步迭代器的本质差异。背压方案是 `asyncio.Queue(maxsize=N)`：满时 `await put` 挂起生产端，背压信号自动沿 put 反传。我的实测：有界 maxsize=3 时生产端被挂起 15 次累计 0.47s、队列峰值 3；无界版挂起 0 次但峰值堆到 13。一句话结论：**无界队列是把背压换成内存泄漏**。我拿 Combine buffer 心智押的「满了继续堆」是错的——Combine 的背压哲学（buffer 策略可配、默认倾向堆）与 asyncio 的「满即挂起」不是一回事，这是本轮人设级墙。

**M5 工程闭环四件**：pytest-asyncio（裸 async 测试只是 coroutine 对象不会跑，插件提供 loop runner，asyncio_mode=auto 一行配置）；logging（级别过滤/多 handler/格式化注入，JSONFormatter 输出单行 JSON 给 ELK/Loki 消费）；uv（Rust 解析器快一到两个数量级、兼管 Python 版本，requirements.txt 与安装命令留痕）；配置（env 优先 + 默认值兜底 + 启动校验 fail fast——缺 LLM_API_KEY 即炸，拒绝带病启动）。

## 二、TaskGroup vs Swift 结构化并发逐项对照表（条款③必交项）

| 维度 | Swift `withTaskGroup` | Python `asyncio.TaskGroup` | 对照结论 |
|------|----------------------|---------------------------|---------|
| 执行底座 | 多线程，子任务可真并行（受核数限） | 单线程事件循环，子任务只是交错执行 | **同构在结构，不在并行**——Swift 的结构化并发给并行，Python 的只给并发 |
| 作用域出口 | 等全部子任务结束才出作用域 | 同 | 同构：出口无孤儿任务，两侧一致 |
| 失败语义 | 任一子任务 throw → 取消其余 → 逐个以 Result/throw 收 | 任一子任务抛异常 → 取消其余 → 出口抛 ExceptionGroup 打包 | Swift 逐个收、Python 打包收；Python 配 `except*` 按类型分拣 |
| 取消送达 | 协作式：Task.isCancelled 轮询检查点，代码自己看旗子 | 异步送达：在下一个 await 点抛 CancelledError | **Swift 要你主动看，Python 直接在你脚下炸**——Python 侧清理靠异常路径自然触发 |
| 清理保证 | defer 在退出路径执行 | finally/async with `__aexit__` 执行（CancelledError 走正常异常路径） | 同构：两侧清理都保，除非清理代码自己阻塞 |
| 父取消传播 | 父任务取消传播到全部子任务 | 同（外层 cancel → TaskGroup 内全体被取消，Q2 实测） | 同构 |
| 非结构化对应物 | 手搓 `Task { }` + 各自 await value | `gather`（等兄弟跑完才抛、异常只传一个） | 两侧都有「自由并发」逃生门，同样的代价：无快速失败、可能留孤儿 |

一句话给同事：**把 Swift 结构化并发的心智整体搬过来是对的（作用域/取消/清理全同构），只有两处要改写——底座从多线程换成单线程协作，失败收集从逐个收换成 ExceptionGroup 打包。**

## 三、给 iOS 同事讲懂（自检段落）

模拟对象：只会 Swift、没写过 Python 的 iOS 同事，场景是「你要转 Python 写 LLM 后端，并发心智我给你，我怕你踩什么」。

**讲法（三句话递进）**：① 你熟悉的 `Task { }` 在 Python 里拆成了两步——调用 async 函数只是拿到一张「待执行说明书」（coroutine 对象），await 或 create_task 才真正开始跑；所以 Swift 里「写了就会跑」的直觉在这里反过来，漏写 await 连编译器都不拦你，只有一行 GC 时的 RuntimeWarning。② 你的 GCD 直觉要整体作废：asyncio 全程一根线程，协程靠主动让出（await）换人跑，一个 time.sleep 就能让全场停摆——我实测过，16 路并发在阻塞调用面前耗时一分不降；真遇到阻塞库，用 run_in_executor 丢线程池（只对 IO 有效，CPU 密集 GIL 挡路）。③ 你熟的 withTaskGroup 可以 90% 平移：作用域、取消传播、清理保证全同构，差异只有两点——取消是在下一个 await 点抛 CancelledError（不是你轮询 isCancelled），失败是 ExceptionGroup 打包（用 `except*` 分拣）。

**自检（能不能过关的三个追问）**：
- 「他听完会犯的最贵错误是什么？」——漏 await 静默缺失：功能没了、报错没有，上线后靠日志查半天。所以我把「写 async 先假设自己会漏 await、测试兜底」列为第一条纪律，Q1 实验②就是亲手把这个错误犯了一遍留档。
- 「哪个 Swift 类比会救他、哪个会害他？」——救：withTaskGroup 心智（结构化并发整体可迁移）。害：GCD「调用即派发」（asyncio 调用不执行）、Combine「buffer 满了继续堆」（asyncio 有界队列满即挂起生产端）——两个错误类比我都押错过、都被实测打脸过，讲的时候必须连坑带解法一起给。
- 「他自己动手时先做什么？」——先跑崩塌表式的对照实验（asyncio.sleep vs time.sleep 扫并发度），一根线程的心智不用背，看一遍耗时曲线就刻进去了。

## 四、全线方法论清单（T1~T6 合订，本轮回填两条）

1. 性质断言兜底（T3 立）：任何数值结论先写断言再信眼睛。
2. 耗时断言必须扫容量/扫并发度，不许单点断言（T5 立，本轮 Q2 崩塌表沿用）。
3. 测量方法学：perf_counter + 重复取 min；跨语言基准先怀疑计时器再怀疑编译器优化（T5 立）。
4. 押注先留档、实测当裁判（本轮收官）：存量框架心智（GCD/Combine）不会自动迁移，四次验证（T1 值语义→T5 别名→T6 漏 await/背压）证明靠纪律兜底而不是靠「记住会踩」。
5. 下笔前自查清单（T5 立）：学过 ≠ 写熟题不犯，清单化比记住可靠。

## 五、遗留缺口（如实记）

- 熔断只讲到边界（错误率阈值→短路冷却）没实现，T6 无后续轮次，记为「已知未练」——若日后接 T7+ 或项目真机线遇到 429 风暴再补实操。
- asyncio.shield（保护收尾操作不被取消波及）本轮没被追问也没写代码，只知用途——同上，记「已知未练」。
