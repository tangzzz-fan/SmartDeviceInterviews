# 资深候选人 · 模拟面试第一轮作答

> 候选人画像：5 年+ iOS 开发，做过智能手环配套 App（EVT 到量产），负责 BLE 通信、OTA、数据同步与稳定性体系，AI-native，英文与硅谷团队日常协作。以下为第一轮 8 题作答（真实经历细节用【占位】标注，数字为估算的已标注）。

## 1. 设备与 App 的状态同步怎么保证不丢不重？

我之前做手环配套 App 时踩过数据丢的坑，后来定了一套机制，核心是「设备端不丢、App 端不重」。

设备端：每一帧数据带单调递增的 seq 和 CRC；未确认的数据会持久化在设备本地环形缓冲里，App 不在线也不丢。App 端：收到数据先落本地库，再回确认，确认里带上「我收到的最新 seq」，设备据此推进。

重连之后做对账：设备告诉 App 它最新的 seq，App 从断点往后拉，靠 seq 去重，天然不重。App 自己也会持久化「哪些数据已确认」，所以 App 被杀重启也能续传。

冲突处理提前定规则：健康数据以设备端为准，用户编辑的标签走版本号合并。量级上，每天几 MB 的心率/睡眠数据，同步成功率在 99.9% 以上（估算）。

## 2. BLE 断连与异常恢复策略？

断连恢复我抓两件事：检测要快、恢复要全。

检测用 didDisconnect 回调 + 自定义 watchdog：连接还在但超过 N 秒没有数据，就判定假死、主动断开重建，避免「看起来连着其实死了」。

重连走状态机，指数退避 1s/2s/4s/8s 封顶加随机抖动；前台间隔短，后台/低电量拉长甚至暂停，防止重连风暴。

恢复现场我有一份 checklist：重新发现服务 → 重订阅 notify → 对账已同步数据 → 续传未完成任务（OTA、上传队列）→ 如果系统清了配对就重新 bonding。

边界规则：用户主动断开绝不自动重连；连续失败后给用户明确提示。指标我盯重连成功率，之前从 85% 提到 97%（估算）。

## 3. OTA 怎么设计？讲中断恢复与回滚。

OTA 我踩过最深的坑就是中断，所以设计时把「中断恢复」当一等公民。

流程：下载固件包先验 MD5/签名 → BLE 分块传输（每包 CRC）→ 传完整体校验 → 切 bootloader → 重启 → 上报新版本。

断点续传：App 记录已传 offset 和包 CRC，重连后从 offset 续传而不是从头再来。固件侧我们推了双 bank（A/B），升级失败自动回滚，变砖概率极低；电量低于 30% 拒绝开始，传输期间防止设备关机。

业务侧还要做进度 UI、前台/后台策略、多设备批量升级队列。这套跑下来升级成功率到 99.x%（估算），返厂升级基本没了。

## 4. 联调出问题，怎么定位是 App 还是固件的锅？

我的方法论是分层隔离，不靠嘴吵。

第一步，nRF Connect 直接对设备发包、读特征：固件行为不对就是固件问题，设备正常再怀疑 App。第二步，App 用桩设备/模拟器单独测，确认解析和逻辑没问题。第三步还定位不了就上 sniffer 抓包，看 ATT 层真实收发——MTU 分包、CCCD 没订阅、字节序这些一眼就能看出来。第四步，把固件 UART 日志和 App 日志按时间线对齐。

印象最深的一次丢包：两边都说是对方的，抓包发现是固件 buffer 溢出——App 发太快没等 ack。后来我们加了流控窗口（比如 20 包一确认）解决。

结论必须带证据：复现步骤 + 抓包 + 日志，修复后回测。

## 5. 设计可穿戴设备的数据同步架构（设备→App→云）

我的设计原则是「App 是网关，先落盘再上传」。

链路：设备 BLE 推数据 → App 每帧验 seq/CRC → 先写本地时序库（GRDB 按天分表）→ 回确认 → 再走云同步（增量 + 幂等键），失败进队列。

补偿三路：后台任务（BGTaskScheduler）拉起、push 到达触发、下次启动对账兜底，任何一路都能把没传完的数据补上。

实时与批量分离：心率这类实时指标前台走实时通道；睡眠、运动这类批量数据后台静默同步，避免前台堆请求耗电。

多设备按时间戳 + 设备 ID 合并，冲突规则提前定好。这样断网、杀 App、换设备都不会丢数据。

## 6. 设计 BLE 自动重连状态机

我会做成纯逻辑状态机，方便单测：idle → scanning → connecting → connected → syncing → backoff，事件驱动加定时器。

参数：退避 1/2/4/8s 加抖动封顶；前台间隔短、后台长；达到最大重试次数就停下，提示用户手动重连。

进入 connected 后触发恢复现场流程：服务发现、订阅、对账、续传。BLE 调用层全部依赖注入 mock，状态机测试不依赖真机。

讲个真实教训：有次线上重连风暴，多台设备同时重连把网关打挂了——因为没有全局退避。后来加了全局互斥和统一退避就稳了。

## 7. AI 怎么融入你的研发流程？举例说明。

AI 在我这不是玩具，是流程的一部分，举三个具体例子：

第一，BLE 状态机和协议解析的单元测试，我让 AI 批量生成骨架，我负责补边界和断言，核心模块覆盖率从 30% 提到 78%（估算）。第二，联调排障时把固件和 App 两份日志丢给 AI 对照，让它先标注时间线差异和可疑字段，我再确认根因，排障时间大概省了 40%。第三，PR 先用 AI 做初审，重点看协议解析、并发、内存这类风险点，它发现问题我再判断。

关键是我的判断力兜底：AI 的建议必须能解释清楚才采纳。团队也沉淀了 AI 使用规范——哪些环节能信 AI、哪些必须人审。

## 8. 英文自我介绍（60 秒）

Hi, I'm Alex, an iOS engineer with five-plus years of experience building companion apps for smart wearables. Most recently I owned the iOS side of a health-band product from EVT to mass production — architecture, BLE communication, OTA, and data sync.

I designed the connection and recovery state machine, the packet protocol together with firmware engineers, and a sync pipeline that guarantees no data loss between device, app, and cloud. I also built the engineering foundation: CI/CD, automated tests, and stability monitoring that kept crash-free sessions above 99.7%.

I'm very AI-native — I use AI for test generation, debugging, and code review every day, and I'm comfortable working in English with distributed teams across time zones.

What excites me about Nirva is combining iOS engineering, hardware collaboration, and 0-to-1 ownership on an AI wearable I genuinely believe in.
