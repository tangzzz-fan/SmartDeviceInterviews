# T6-01 教练出题：async 与企业落地（显式增量轮）

> 教练 agent 出题稿（题干版，两分支共有）。评分要点、三级提示与参考答案见 `T6-01-教练密卷-async与企业落地.md`（仅教练分支，学员禁阅）。
> 原料说明：本轮是学员明确要求的显式增量轮，考法回到 T4 式「机制空白检测」——Swift Concurrency 存量是双刃剑：结构化并发方向感能迁移，但 asyncio 的「协程是对象」「单线程协作调度」与 Swift 模型有本质差异，**拿 GCD/Swift Concurrency 硬翻的地方就是考点**。
> 作答规则：闭卷硬推，卡住逐级要提示（弱→中→强），绝不直接要答案（C1/C2）；概念题与代码题分开判定（C3）。
> **复习线特别条款**：① T5 遗留观察项「学过 ≠ 写熟题不犯」本轮继续盯——Combine/GCD 心智在 async 代码里预期同类复发；② 沿用全线纪律：性质断言兜底、耗时断言必须扫容量（Q2 阻塞崩塌实验强制扫并发度）、测量方法学（perf_counter+重复取 min）；③ 费曼稿必须含「给 iOS 同事讲懂」自检段落与「TaskGroup vs Swift 结构化并发逐项对照表」（路线 Phase 6 关键对比任务）。

## 一、共识模型（教练版五个骨架）

学员先自推五模型再对本版，标注差异。

| # | 模型 | 一句话骨架 |
|---|------|-----------|
| M1 | 协程是对象，不是调用 | `async def` 调用后返回 coroutine 对象**不执行**，要 await（当前协程让出）或 create_task（丢进事件循环排队）才跑；漏写 await 得到对象不报错——静默翻车点 |
| M2 | 单线程事件循环 = 协作式调度 | 全 loop 一根线程，谁阻塞谁杀全场（time.sleep/同步 requests 卡死整个并发）；真阻塞的逃生口是 run_in_executor（线程池）——GCD「丢另一队列」的本能没有直接对应物 |
| M3 | 结构化并发三件套 | Semaphore 限流（并发数闸门）、asyncio.timeout（超时即 CancelledError）、TaskGroup（一个挂全组取消+异常聚合）——与 Swift withTaskGroup 同构但 API 细节不同 |
| M4 | async 迭代 = 流式消费的协议 | async for 背后是 `__aiter__`/`__anext__` 协议，异步生成器（async def + yield）是 LLM 流式 token 消费的标准形态；背压靠有界缓冲（asyncio.Queue(maxsize)） |
| M5 | 工程闭环 = pytest+logging+uv+配置分层 | 异步测试要 pytest-asyncio（或 pytest 原生 async 支持）；logging 替代 print（级别/结构化/落盘）；uv 管依赖；环境变量+默认值分层的配置模式 |

## 二、争议焦点（三题，考有边界的立场）

- **F1**：gather vs TaskGroup——错误处理语义（gather 默认等其他全跑完 vs TaskGroup 快速失败）、取消传播、结构化作用域，各自适用场景给立场；Swift 侧类比（withTaskGroup vs 手搓 Task）挂靠。
- **F2**：IO 密集用 asyncio、CPU 密集怎么办——multiprocessing/线程池/run_in_executor 的判据；GIL 在 asyncio 场景里的实际影响讲清（T1 观察项收官）。
- **F3**：限流重试的边界——客户端 Semaphore 限流 vs 指数退避重试 vs 服务端限流配合；重试风暴怎么防（抖动/退避上限/熔断），给一套可落地的组合拳。

## 三、拷问题——概念口述通道（C1–C6）

**C1（M1）**：协程对象三连——① 调用 `async def f()` 到底发生了什么（返回什么、执行了吗）？② 漏写 await 会怎样、为什么不报错？③ await 与 create_task 的区别（当前协程挂起等结果 vs 丢进 loop 立即返回 Task）——Swift 类比挂靠：哪个像 `await task.value`、哪个像 `Task { }`？

**C2（M2）**：阻塞杀 loop——① 在协程里调 `time.sleep(5)` 会发生什么、为什么「再开一个协程」救不了？② 为什么 GCD 的「丢到另一个队列」本能在 asyncio 里没有直接对应物（调度模型差异）？③ run_in_executor 的机制与适用边界（什么阻塞值得丢线程池、什么该换异步库）？

**C3（M3）**：取消语义对照——① asyncio.TaskGroup 里一个任务抛异常，其他任务与组的命运（取消、聚合异常 ExceptionGroup）？② Swift withTaskGroup 的取消传播与之逐项对照（同构点与差异点各至少两条）；③ 被取消的协程里 finally/async with 的清理保证讲到什么程度？

**C4（M3）**：API 网关三件套——① Semaphore 限流的机制（acquire/release 与 async with，为什么它不排队发请求而是卡入场）；② asyncio.timeout 的实现原理（取消任务+CancelledError）与「超时后资源清理」的关系；③ 重试为什么要指数退避+抖动，固定间隔重试在什么场景会制造灾难？

**C5（M4）**：async 迭代——① `async for` 背后的协议（`__aiter__`/`__anext__`，与同步 `__iter__`/`__next__` 的逐项对照）；② 异步生成器怎么写（async def + yield）、它的挂起语义（yield 处让出控制权给谁）；③ LLM 流式消费里「生产快消费慢」怎么办——背压方案给一个并说清有界队列满时的行为。

**C6（M5）**：工程化四连——① 异步函数怎么写测试（pytest 怎么跑协程，裸 `assert await f()` 为什么不行）；② logging 比 print 强在哪三条（级别/输出目标/格式化），结构化日志（JSON）给个落地形态；③ uv 与 pip 的区别讲到机制层（解析器/锁文件/速度）；④ 配置分层：环境变量 + 默认值 + 校验（pydantic-settings 或手写 dataclass 从 env 读），与 iOS 的配置方案（xcconfig/Info.plist 分环境）做类比挂靠。

## 四、拷问题——代码任务通道（Q1–Q4）

代码要求：一律用 `.venv/bin/python` 跑通，输出贴回作答稿；文件落 `代码/T6/`，文件头注释标对应题号与撞墙记录。挂靠项目见 [[02-项目驱动实践路线.md|项目路线]] Phase 6。pytest 若未装，走 uv 安装并记录（6.4 考点之一）。

**Q1（挂项目 6.1，M1/M3）**：**asyncio 基础实验集**。最小实验证明：① 调用 async def 不执行（打印证据+coroutine 类型证据）；② 漏写 await 的静默翻车现场（RuntimeWarning 留档）；③ gather vs TaskGroup 的错误处理差异（一个任务抛异常时两者行为实测对照）；④ TaskGroup 取消传播实验（子任务被取消时 finally 清理是否执行）。

**Q2（挂项目 6.2，M2/M3）**：**并发 LLM API 网关（mock）**。mock 一个异步 API（asyncio.sleep 模拟网络延迟+随机失败率），实现 Semaphore 限流 + 指数退避重试 + asyncio.timeout + TaskGroup 结构化取消的调用器；**必须实测阻塞调用杀 loop**：同一并发度下，API 实现里塞 time.sleep（模拟阻塞 SDK）前后的总耗时对比，并发度扫 {1, 4, 16} 三档（沿用 T5「扫容量」纪律）。

**Q3（挂项目 6.3，M4）**：**流式响应消费管道**。异步生成器模拟逐 token 流式输出（带随机间隔），async for 消费；加有界 asyncio.Queue 做背压缓冲，实测「缓冲满时生产端被阻塞」的行为证据（时间戳对照）；对比有界 vs 无界的内存/行为差异给出结论。

**Q4（挂项目 6.4，M5）**：**工程化基础**。① pytest 覆盖 Q2/Q3 的关键路径（重试成功路径/超时路径/取消路径/背压路径，至少四个用例，异步测试方案落地）；② logging 结构化日志（JSON 行格式）替换所有 print；③ uv 依赖清单（pyproject 或 requirements 均可，记录安装命令）；④ 配置从环境变量读取（含默认值与缺省校验）。全部实跑留输出。
