# T6-01 教练密卷：async 与企业落地（仅教练分支，学员禁阅）

> 配套题干：`T6-01-教练出题-async与企业落地.md`。本文件含判分点、弱/中/强三级提示、复习线变式题、失真自查清单。
> 本轮判定基准：机制空白检测（T4 式）——**能用 Swift 类比说对方向但 asyncio 机制讲错 = 半过**；类比本身错误（如「协程像 DispatchQueue.async」当结论用）= 未过信号，但按人设纪律类比错误如实保留不扣态度分。
> 人设卡对拍锚点（01-学员人设卡.md T6 节原文）：「协程是对象，调用 async def 不执行、要 await 或建 task 才跑」会踩；await 漏写得到 coroutine 不报错会翻车；阻塞调用杀 loop 不知道严重性、run_in_executor 是盲区；并发控制方向能讲（Swift 结构化并发存量）但 API 细节生疏；企业落地面（pytest/logging/uv/配置）停留名词层。首轮预期：C1/C2 高发未过或半过，C3 方向过细节半，C6 名词层半过。

## 一、概念题判分点与提示梯

### C1 协程对象三连
- **判分点**：① 调用返回 coroutine 对象、函数体一行没跑（要证据级理解：print 在函数体内不会输出）；② 漏 await：对象被创建又被丢弃，只有 GC 时 RuntimeWarning「coroutine was never awaited」，**运行时不报错、功能静默缺失**——这是与 Swift 的关键差异（Swift 里悬挂的 async 调用编译器直接警告/报错）；③ await = 当前协程挂起等结果（顺序依赖用它），create_task = 立即排入 loop 并发跑（返回 Task 句柄）；Swift 挂靠：await ≈ `await task.value`，create_task ≈ `Task { }` 启动（但 asyncio 单线程协作，Task 不会真并行）。
- **弱提示**：写一行 `f()`（不 await）然后打印返回值，类型是什么？函数体里的 print 跑了吗？
- **中提示**：Swift 里忘记 await 编译器拦你；Python 这里谁来拦？
- **强提示**：协程是「待执行的说明书」，await/task 才是「按下执行键」；没人按键，说明书只会在被当垃圾回收时抱怨一句。
- **复习线变式**：`asyncio.run(f())` 与「在协程里再 asyncio.run」为什么后者报错？（loop 嵌套禁止；loop 是单实例资源。）

### C2 阻塞杀 loop
- **判分点**：① time.sleep 卡住的是**整根线程 = 整个 loop**，所有协程停摆（不是只卡自己），因为协作式调度下没人能让出控制权；「再开协程」救不了——协程是同一根线程上的排队，不是新线程；② GCD 类比失效的根源：GCD 是抢占式多线程、队列背后是线程池；asyncio 是单线程协作式，「丢到另一个队列」的对应物**不存在于协程层**，只能显式 run_in_executor 丢线程池；③ run_in_executor 机制（loop.run_in_executor(None, fn) → 默认 ThreadPoolExecutor，返回 awaitable）与边界：IO 阻塞 SDK/文件 IO 值得丢池子（GIL 在 IO 等待时释放），CPU 密集丢线程池没用（GIL）要 multiprocessing。
- **弱提示**：asyncio 有几根线程在跑你的协程？
- **中提示**：time.sleep 期间，其他协程在干什么？谁负责切换它们？
- **强提示**：协作式调度 = 每个协程自己决定何时让出（await 点）；阻塞调用没有 await 点，调度器永远等不到让出。
- **复习线变式**：为什么 aiohttp 存在、直接用 requests 在异步代码里就是错的？（requests 的 socket recv 是阻塞系统调用，包一层协程壳也救不了——必须真异步 IO 或 executor。）

### C3 取消语义对照
- **判分点**：① TaskGroup 内任一任务抛异常 → 取消组内所有存活任务 → with 块出口抛 ExceptionGroup 聚合所有异常；② 与 Swift 同构点：结构化作用域（出口等全部子任务结束）、失败取消兄弟任务、父取消传播到子；差异点：Swift 用 Result/throw 逐个收、asyncio 用 ExceptionGroup 打包；Swift 的 Task.isCancelled 轮询 vs asyncio 的 CancelledError 在下一个 await 点抛出（**取消是异步送达的，不是立即终止**）；③ 清理保证：CancelledError 在 await 点抛出后走正常异常路径，finally/async with 的清理**会执行**——除非清理代码里又有阻塞或再次取消。
- **弱提示**：TaskGroup 里一个任务炸了，其他任务是继续跑还是被叫停？
- **中提示**：取消是怎么「送达」给正在 await 的任务的？（对比 Swift 的 isCancelled 检查点）
- **强提示**：取消 = 在目标任务的下一个 await 点抛 CancelledError；所以 finally 有机会跑，但取消不是断电。
- **复习线变式**：`asyncio.shield` 是干什么的？（保护内部 awaitable 不被外层取消波及——如收尾的落盘操作。）

### C4 API 网关三件套
- **判分点**：① Semaphore 是计数器闸门：async with sem 入场 -1、出场 +1，值为 0 时后续协程在 await acquire 处挂起——限的是「同时在场数」不是「发送速率」（速率限制要靠令牌桶，说清边界加分）；② asyncio.timeout(n) = 到期取消目标任务，CancelledError 沿任务传播，资源清理靠任务内 try/finally 与 async with 的 `__aexit__`；③ 指数退避+抖动：固定间隔重试在服务端抖动/过载时形成**重试风暴同步化**（所有客户端同一时刻重发，二次打爆），指数拉开+随机抖动打散相位；要有退避上限与总重试预算。
- **弱提示**：Semaphore(10) 意味着同一时刻最多几个请求在飞？第 11 个请求者在哪等？
- **中提示**：1000 个客户端同时失败，都固定 2s 后重试，服务端 2s 后会看到什么？
- **强提示**：限流管「入场并发」，退避管「失败再来的节奏」，两者维度不同都要有。
- **复习线变式**：限「每秒请求数」（速率）与限「并发数」分别用什么结构？（令牌桶/漏桶 vs Semaphore。）

### C5 async 迭代
- **判分点**：① async for 调 `__aiter__` 拿迭代器、反复 await `__anext__`（StopAsyncIteration 终止）——每次 anext 都是一个挂起点，这是与同步迭代器的本质差异（同步 next 不能让出控制权）；② 异步生成器 = async def + yield，yield 处挂起把控制权还给事件循环（消费者拿到值），下次 anext 恢复执行；③ 背压：asyncio.Queue(maxsize=N)，满时 `await put` 挂起生产端——背压信号自动沿 put 反传到生产侧；无界队列 = 生产快消费慢时内存无上限增长。
- **弱提示**：同步 for 的每一步能让出 CPU 吗？async for 呢？
- **中提示**：异步生成器 yield 之后，控制权去了哪里、谁叫它回来？
- **强提示**：有界 Queue 的 put 在满时挂起 = 免费的背压；无界队列是把背压换成内存泄漏。
- **复习线变式**：async 生成器能不能用 `return` 带值？（不能，只能 StopAsyncIteration；与同步生成器一致。）

### C6 工程化四连
- **判分点**：① pytest 里协程不会自动跑：裸 async test 函数只会被收集成 coroutine 对象不执行（PytestUnhandledCoroutineWarning），要 pytest-asyncio（@pytest.mark.asyncio / asyncio_mode=auto）或 anyio 插件提供 loop；② logging 三条：级别过滤（DEBUG/INFO 分环境）、多输出目标（handler：控制台/文件/远端）、格式化注入（时间/模块/trace_id）；结构化日志 = JSONFormatter 或 python-json-logger，字段可被 ELK/loki 消费；③ uv：Rust 写的解析器+安装器、全局/锁文件解析快 10-100×、能管 Python 版本本身；pip 只做安装、解析慢且无内置锁；④ 配置分层：env 变量优先+代码默认值兜底+启动时校验（缺必填 fail fast）；类比 iOS：env=xcconfig 分环境、默认值=Info.plist 基线、校验=启动时 precondition。
- **弱提示**：pytest 收集到一个 async def 测试函数，直接调用它会得到什么？
- **中提示**：print 上线后想按级别关掉调试输出、想同时写文件，做得到吗？
- **强提示**：异步测试缺的是「谁来跑这个 loop」——插件就是那个 runner。
- **复习线变式**：logging 的 logger 层级传播（propagate）会导致什么经典 bug？（日志打两遍；子 logger 向父冒泡。）

## 二、争议焦点判分点

- **F1 gather vs TaskGroup**：gather 是「自由并发」——return_exceptions=False 时一个挂其余照跑到结束才抛（资源浪费）、异常只有一个能传出；TaskGroup 是「结构化并发」——快速失败、取消兄弟、ExceptionGroup 全量聚合、作用域出口保证无孤儿任务。立场：新代码默认 TaskGroup；gather 留给「互不相关、允许部分失败、要逐个收结果」的旧场景。Swift 挂靠：gather ≈ 手搓多个 Task + await 各自 value，TaskGroup ≈ withTaskGroup。
- **F2 IO/CPU 分工**：asyncio 吃 IO 密集（等待时让出，一根线程扛万级并发）；CPU 密集在 asyncio 里是毒（占住 loop），要 multiprocessing（绕 GIL、多进程）或 run_in_executor 的 **ProcessPool**；线程池只对「阻塞 IO 适配」有效。GIL 收官表述：GIL 让线程池对 CPU 密集无效、让 multiprocessing 成为 CPU 并行唯一标准答案；asyncio 不受 GIL 额外伤害（本来就单线程），但也从不提供并行。
- **F3 限流重试组合拳**：入场 Semaphore 限并发（保护自己也保护服务端）+ 指数退避带抖动（防风暴同步化）+ 退避上限与总预算（防无限重试）+ 服务端 429 时尊重 Retry-After；熔断是进阶（错误率阈值→短路冷却）。三层「限并发/控节奏/有预算」齐 = 过。

## 三、代码题判分点

- **Q1**：四个实验都要有**输出证据**（coroutine 类型打印/RuntimeWarning 文本/gather 与 TaskGroup 行为差异的具体输出/finally 清理打印）；实验②的 RuntimeWarning 必须真实留档（-W default 或 asyncio.run 后 GC 触发）；取消实验要证明 finally 跑了。
- **Q2**：网关四件套齐全且**可组合**（限流+重试+超时+取消不互相打架）；阻塞崩塌实验必须有并发度扫描表（{1,4,16}×{async sleep, time.sleep}），time.sleep 版应展示「并发度加大耗时不减反增/持平」的崩塌曲线；重试要用可注入的随机失败 mock（可复现，seed 固定）。
- **Q3**：背压证据必须是时间戳级的（生产端 put 被挂起的起止时间），不是嘴上说；有界 vs 无界对比要有可观测差异（队列峰值长度/内存行为/消费完成时间）；async 生成器的随机间隔要有 seed。
- **Q4**：四个用例路径齐全且**真跑通过**（pytest 输出留档）；JSON 日志要真有一行 JSON 输出证据；uv 安装命令记录真实（pytest/pytest-asyncio 走 uv pip install）；配置缺省校验要有 fail fast 实测（缺环境变量时报错退出）。

## 四、失真自查清单（阅卷时跑）

1. 机制空白轮失真信号：概念全秒答 = 可疑（人设卡明示 C1/C2 会踩），抽查 Q1 实验②的 RuntimeWarning 是否真实（当场复跑）。
2. 撞墙记录真实性：Q2 阻塞崩塌表当场复跑一格验证量级；Q3 背压时间戳可复现（seed 固定）。
3. Swift 类比纪律：类比错误是否如实保留在作答稿（按人设卡第五条，事后自我修正 = 失真信号）。
4. pytest 生态真伪：`.venv/bin/python -m pytest --version` 与用例数可当场验证；uv 安装命令留痕。
5. 密卷隔离：`git ls-tree -r --name-only feat/mit-python-study-student | grep 密卷` 应为空。
