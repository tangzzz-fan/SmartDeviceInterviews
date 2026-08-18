# T6-02 学员作答：async 与企业落地（显式增量轮）

> 学员 agent 作答稿（闭卷，按 [[01-学员人设卡.md|人设卡]] 如实发挥）。自评三档：**有把握 / 半懂半猜 / 纯猜**。
> 代码一律 `.venv/bin/python` 实跑（Python 3.12.13，pytest 9.1.1 + pytest-asyncio 1.4.0 经 uv 安装），输出贴于第四节；撞墙记录在代码文件头。Swift Concurrency 类比按人设纪律如实保留（含错的）。

## 〇、五模型自推（先写再对本）

自推版本：① async def 定义异步函数，await 等结果——和 Swift async 一样吧；② 事件循环就是个调度器，类似主线程 RunLoop；③ 并发控制有 Semaphore、timeout、TaskGroup，Swift 结构化并发我熟，方向都能说；④ 流式就用 for 循环一个个拿；⑤ pytest 测试、logging 打日志、uv 装包，名词都知道。

对教练版差异：M1 我把「async def 和 Swift async 一样」写出去的瞬间就该知道不对——**调用 async def 不执行**这层我完全没有（Q1 实验①实测返回 coroutine 对象、函数体一行没跑，墙2 留档）；M2「类似 RunLoop」的类比停在表面，**阻塞杀 loop 的严重性**是 Q2 崩塌表教给我的；M4「for 循环一个个拿」漏了 async for 的挂起语义和背压；M5 确实停在名词层，C6 见下。

## 一、概念口述通道

**C1（协程对象三连）**：① 调用 `async def f()` 返回 coroutine 对象，函数体一行不执行——我是写完 Q1 实验才敢确认的，写之前拿 Swift 心智以为「调用就开始跑」。② 漏 await：对象被造出来又被丢弃，运行时不报错，只在 GC 时给一行 RuntimeWarning: coroutine was never awaited——**静默缺失**，Swift 里编译器直接拦，这里没人拦，这是我觉得最危险的差异。③ await 挂起当前协程等结果（像 Swift 的 `await task.value`）；create_task 把协程丢进 loop 立即返回 Task 句柄（像 `Task { }`）——但 asyncio 是单线程协作，Task 不会真并行，这点 Swift 类比会误导。自评：**半懂半猜**（方向靠类比拼，机制是实验砸出来的）。

**C2（阻塞杀 loop）**：① time.sleep 卡住整根线程 = 整个 loop，所有协程停摆——「再开一个协程」救不了，因为协程只是同一根线程上的排队。② GCD 类比失效：GCD 队列背后是线程池、抢占式；asyncio 协程层没有「另一个队列」，只能 run_in_executor 显式丢线程池。③ run_in_executor：`loop.run_in_executor(None, fn)` 默认 ThreadPoolExecutor，返回 awaitable；IO 阻塞（同步 SDK、文件 IO）值得丢池子（GIL 在 IO 等待时释放），CPU 密集丢线程池没用（GIL）得上 multiprocessing。②③是本轮人设盲区，首答只说到「阻塞不好要换异步库」，run_in_executor 的 API 和边界是提示后补的。自评：**半懂半猜**。

**C3（取消语义对照）**：① TaskGroup 一个任务抛异常 → 取消所有存活任务 → with 出口抛 ExceptionGroup（Q1 实验④实测）。② 与 Swift withTaskGroup 同构点：结构化作用域出口等全部子任务、失败取消兄弟、父取消传播到子；差异点：Swift 逐个 throw/Result 收，Python 用 ExceptionGroup 打包（`except*` 语法）；Swift 用 Task.isCancelled 轮询检查点，asyncio 的取消是在下一个 await 点抛 CancelledError——**取消是异步送达不是立即终止**。③ 清理保证：CancelledError 走正常异常路径，finally/async with 清理会执行（Q1 实验④两行 finally 打印为证），除非清理代码里又阻塞。自评：**有把握**（结构化并发存量迁移成功，差异点是现场对的）。

**C4（API 网关三件套）**：① Semaphore 是计数器闸门，async with 入场 -1 出场 +1，值为 0 时后来者在 acquire 处挂起——限的是「同时在场数」不是「每秒请求数」（后者要令牌桶，这层边界是提示后补的）。② asyncio.timeout(n) 到期取消目标任务，CancelledError 沿任务传播，清理靠任务内 try/finally 与 async with 的 `__aexit__`（Q2 超时路径实测 ExceptionGroup 聚合 2 个超时）。③ 固定间隔重试在服务端抖动时形成重试风暴同步化（1000 个客户端同一时刻重发二次打爆），指数退避拉开间隔、随机抖动打散相位，还要退避上限和总预算。自评：**半懂半猜**（①②机制过，令牌桶边界和风暴量化是补的）。

**C5（async 迭代）**：① async for 背后 `__aiter__`/`__anext__`，每次 anext 是挂起点——与同步 `__iter__`/`__next__` 的本质差异就是「每步能让出控制权」。② 异步生成器 = async def + yield，yield 处挂起把控制权还给事件循环，消费者下次 anext 时恢复。③ 背压：asyncio.Queue(maxsize=N)，满时 `await put` 挂起生产端——背压信号沿 put 反传；无界队列（maxsize=0）= 生产快消费慢时内存无上限。Q3 实测：有界 maxsize=3 时生产端被挂起 15 次累计 0.47s，无界版挂起 0 次峰值堆到 13——我拿 Combine buffer 心智押的「满了继续堆」是错的（墙1 留档）。自评：**半懂半猜**（协议名说得对，背压哲学押错）。

**C6（工程化四连）**：① 裸 async 测试函数 pytest 收集了不会跑（只是个 coroutine 对象），要 pytest-asyncio 提供事件循环 runner——asyncio_mode=auto 一行配置全过。② logging 三条：级别过滤、多 handler 输出目标、格式化注入（时间/模块/自定义字段）；JSON 结构化 = 自定义 Formatter 输出单行 JSON，ELK/Loki 可消费（Q4 jsonlog.py 落地）。③ uv：Rust 写的解析器+安装器、快一到两个数量级、还能管 Python 版本；pip 只管安装解析慢。④ 配置分层：env 优先 + 代码默认值 + 启动校验 fail fast；类比 iOS：env=xcconfig 分环境、默认值=Info.plist 基线、校验=启动 precondition。自评：**半懂半猜**（②④靠 iOS 经验挂靠能说到机制，①③是名词层升级上来的）。

## 二、争议焦点

**F1（gather vs TaskGroup）**：gather 是自由并发——一个任务挂了其余照跑到结束才抛（Q1 实验③实测：g1/g2 都完成才抛），异常还只能传出一个；TaskGroup 是结构化并发——快速失败、取消兄弟、ExceptionGroup 全量聚合、出口无孤儿。立场：新代码默认 TaskGroup；gather 留给「互不相关、允许部分失败、要逐个收结果」的场景。Swift 挂靠：gather ≈ 手搓多个 Task 各自 await value，TaskGroup ≈ withTaskGroup。自评：**有把握**（Q1 数据背书）。

**F2（IO/CPU 分工与 GIL 收官）**：asyncio 吃 IO 密集——等待时让出，一根线程扛万级并发；CPU 密集在 asyncio 里是毒（占住 loop 全场停摆），要 multiprocessing 绕 GIL 或 run_in_executor 的 ProcessPool；线程池只对「阻塞 IO 适配」有效。GIL 收官表述（T1 观察项）：GIL 让线程池对 CPU 密集无效、让 multiprocessing 成为 Python CPU 并行的唯一标准答案；asyncio 不受 GIL 额外伤害（本来就单线程），但也从不提供并行——**并发 ≠ 并行**，asyncio 给的全是并发。自评：**有把握**。

**F3（限流重试组合拳）**：三层——① 入场 Semaphore 限并发（保护自己也保护服务端，Q2 网关里重试退避也在闸门内，防重试风暴占满名额）；② 指数退避带抖动（防风暴同步化）；③ 退避上限 + 总重试预算（防无限重试），服务端给 429 Retry-After 时尊重它。熔断是进阶（错误率阈值→短路冷却），这轮没实现只讲到。自评：**有把握**（组合拳在 Q2 里全部落地过）。

## 三、自评汇总

概念：C3/F1/F2/F3 有把握（4 项，结构化并发存量迁移区），C1/C2/C4/C5/C6 半懂半猜（5 项，机制空白区）——与人设卡「C1/C2 高发、企业面名词层」的预判吻合，无未过（提示梯逐级补上了）。本轮类比纪律执行情况：GCD「调用即派发」、Combine「buffer 无限堆」两个错误类比如实保留在作答与代码墙记录里，未事后修饰。

## 四、代码任务通道（实跑输出）

**Q1 asyncio 基础实验集**（`代码/T6/Q1-asyncio基础实验集.py`）：四实验全过，关键输出——

```
实验①：返回值类型: <class 'coroutine'>（函数体 print 没跑）
实验②：拿到的 data: <coroutine object fetch at 0x...>
        RuntimeWarning: coroutine 'fetch' was never awaited（退出码 0）
实验③：[g1] 完成 / [g2] 完成 / gather 抛出（等兄弟跑完才抛）
        ----
        TaskGroup 抛出 ExceptionGroup（t1/t2 连「完成」都没打到就被取消）
实验④：[L1] finally 清理执行 ✓ / [L2] finally 清理执行 ✓ / 无孤儿任务
```

撞墙 2 处：墙1 对照组时序设计错（bad_task 先炸演示不出 gather 的等待本性，同 T3-Q3 教训复发）；墙2 人设翻车留档（漏 await 真写了，静默缺失实锤）。

**Q2 并发 LLM API 网关**（`代码/T6/Q2-并发LLM网关与阻塞崩塌.py`）：

```
网关：20 任务/并发4/失败率30% 全部成功（重试兜底），耗时 0.94s
超时路径：TaskGroup 聚合了 2 个超时异常 ✓
取消路径：外部 cancel → TaskGroup 内全体任务被取消 ✓

阻塞崩塌实验（任务数=16，单次时长=0.1s）
   并发度 |  asyncio.sleep 版 |   time.sleep 版
     1 |         1.617s |       1.655s
     4 |         0.404s |       1.659s
    16 |         0.101s |       1.659s
```

崩塌曲线实锤：异步版 16 路并发 16 倍加速，time.sleep 版并发度加到 16 耗时一分不降（1.655→1.659s）——墙1 的 GCD 押注（「16 并发该并行」）被实测打脸。撞墙 2 处（押注错 + run_n 漏传 rng 首跑 AttributeError）。

**Q3 流式消费与背压**（`代码/T6/Q3-流式消费与背压.py`）：

```
直连消费：async for 拿到 10 token，耗时 0.68s ✓
有界队列 maxsize=3：队列峰值长度 = 3，生产端被挂起 15 次累计 0.47s
  挂起明细：tok-5: 11ms / tok-6: 39ms / tok-7: 30ms
无界队列 maxsize=0：队列峰值长度 = 13，生产端被挂起 0 次
```

背压证据是时间戳级的。撞墙 1 处：Combine buffer 心智押错（满时挂起生产端 vs 无限堆积）。

**Q4 工程化基础**（`代码/T6/Q4-工程化/`）：

```
uv pip install --python .venv/bin/python pytest pytest-asyncio
  + pytest==9.1.1 + pytest-asyncio==1.4.0

pytest：6 passed in 0.99s
  重试成功 / 超时聚合 / 取消传播 / 背压有界vs无界 / 配置 fail fast / env 覆盖默认值

JSON 日志样例（demo.py 实跑）：
{"ts": "...", "level": "WARNING", "logger": "llm.gateway", "msg": "retry_scheduled",
 "task_id": "t1", "attempt": 0, "backoff_ms": 5.3}
{"ts": "...", "level": "ERROR", "logger": "llm.demo", "msg": "config_rejected",
 "reason": "缺必填配置 LLM_API_KEY……fail fast，拒绝带病启动"}
```

四件套落地：pytest-asyncio auto 模式（pytest.ini）+ JsonFormatter 单行 JSON + requirements.txt 与 uv 安装命令留痕 + dataclass 配置从 env 读取（缺 LLM_API_KEY 启动即炸，fail fast 有实测）。

撞墙总计：Q1 两处 + Q2 两处 + Q3 一处 + Q4 零处（工程化是存量手感区，但 C6 自评如实降到半懂半猜——写得出 ≠ 讲到机制）= **5 处**，全部有真实输出/报错留档；两堵人设级墙（漏 await 静默缺失、Combine 背压哲学押错）与 T5 遗留观察项「学过 ≠ 写熟题不犯」形成呼应。
