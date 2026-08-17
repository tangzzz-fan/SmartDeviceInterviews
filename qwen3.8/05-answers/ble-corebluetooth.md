# BLE / Core Bluetooth 专项 参考答案

> 来源：题库 `qwen3.8/03-question-bank/ble-corebluetooth.md`（Q1-Q12 全量作答），与 `qwen3.8/01-jd-analysis/jd-breakdown.md` 的权重对策对齐。
> 身份设定：8 年+ iOS、可穿戴 BLE 全链路经验的资深候选人，第一人称口语化作答。
> 注：实战案例为示范稿，末尾带 `<!-- 需替换为真实经历 -->` 的题需替换为本人真实经历。

## Q1. 讲一遍 BLE 设备从扫描到数据收发的完整链路。

**结论先行**：链路是 CBCentralManager 上电 → 扫描发现 → connect → 服务发现 → 特征值发现 → 读写/订阅收发，每一步都是异步回调驱动，核心是把状态机串起来而不是裸调 API。

**原理展开**：先初始化 `CBCentralManager` 并指定 delegate 和 queue，等 `centralManagerDidUpdateState` 报 `poweredOn` 才能调 `scanForPeripherals(withServices:options:)`——建议必须传服务 UUID 过滤并设 `CBCentralManagerScanOptionAllowDuplicatesKey` 为 false，省电且减少重复回调。扫到目标后调 `connect(_:options:)`，成功走 `didConnect`，失败或超时走 `didFailToConnect` / `didDisconnectPeripheral`。连接建立后第一件事是 `discoverServices`，拿到 service 再 `discoverCharacteristics`，注意按需发现、别全量 discover 所有服务，既慢又可能触发部分芯片的兼容问题。数据收发三种方式：`readValue` 一次性读；`writeValue(_:type:)` 写，`withResponse` 有 ACK、`withoutResponse` 要配合 `canSendWriteWithoutResponse` 和 `peripheralIsReady(toSendWriteWithoutResponse:)` 做流控；`setNotifyValue(true)` 订阅后数据从 `didUpdateValueFor` 推上来。连接参数（interval / slave latency / supervision timeout）由从机请求、主机决定，interval 越短延迟越低但越耗电，可穿戴常在前台请求短 interval、后台请求长 interval（用 `CBPeripheralManager` 侧的 connection parameter request）。

**实战案例**：我做手环 App 时把整条链路封装成了一个连接状态机：idle → scanning → connecting → discovering → connected，每个状态迁移都打点上报，配合 `CBConnectPeripheralOptionNotifyOnDisconnectionKey` 做断连通知。上线后靠这套埋点把首次连接成功率从约 92% 优化到 98% 以上，主要收益来自扫描加服务过滤、发现流程按需裁剪，以及失败后自动重试一次。<!-- 需替换为真实经历 -->

**边界与权衡**：这条链路每一步都可能卡住——扫描无结果、connect 挂起、discover 超时，所以每个环节都要有超时兜底和可取消的设计；另外 iOS 的回调都在你传入的 dispatch queue 上，队列设计不当（比如用主队列做大量数据解析）会造成 UI 卡顿，我会把 BLE 回调放在专用串行队列上。

## Q2. CBCentralManager 的状态机有哪些状态？状态切换时你的 App 该怎么处理？

**结论先行**：六个状态 `unknown / resetting / unsupported / unauthorized / poweredOff / poweredOn`，只有 poweredOn 可用，其余每个状态都要有明确的用户引导或恢复路径，而且状态随时可能变，所有 BLE 操作前必须检查当前态。

**原理展开**：`unknown` 是冷启动瞬间的过渡态；`resetting` 表示系统蓝牙子系统重置，此时所有连接和 pending 操作都作废，正确做法是清空内部状态、等回到 poweredOn 后重建；`unsupported` 是设备不支持 BLE（现在基本绝迹）；`unauthorized` 是用户没授权蓝牙权限（iOS 13+ 的 `NSBluetoothAlwaysUsageDescription`），应引导去系统设置；`poweredOff` 引导用户开蓝牙。关键是 `centralManager(_:willRestoreState:)` 配合 restoration 从后台恢复时也会重新走 updateState。工程上我把这些状态收敛到一个 `BluetoothAvailability` 枚举，UI 层只订阅这个抽象，不直接碰 CB 的原始状态。

**实战案例**：我们遇到过 poweredOff 时用户正在同步数据的投诉。处理方案是：传输层在写数据前检查 manager state，poweredOff 或 resetting 时立即中止任务并持久化进度（同步到第几条记录），等状态恢复 poweredOn 且连接重建后从断点续传，UI 上提示"蓝牙已关闭，恢复后自动继续"。这样把"中断"从失败变成了可恢复事件，相关客诉基本清零。<!-- 需替换为真实经历 -->

**边界与权衡**：最容易踩的坑是初始化时序——`CBCentralManager` 的 delegate 是初始化时传入的，但 `didUpdateState` 是异步的，任何在状态回调前发起的操作都要排队。我用一个 promise/continuation 队列把 poweredOn 之前的 API 调用挂起，超时则失败，避免调用方自己各自处理"还没就绪"的问题。代价是这套封装比裸调 CB 复杂，小项目可能过度设计。

## Q3. 设备连接不稳定、频繁断连，你会怎么设计重连与恢复机制？

**结论先行**：核心思路是"区分断开原因 + 指数退避主动重连 + 利用系统后台自动重连 + 恢复后增量补数据"，重连不是死循环 retry，而是一套有预算、可放弃的策略。

**原理展开**：`didDisconnectPeripheral` 会带 `error`：error 为 nil 通常是本端主动断开，非 nil（CBError 域，如 connection timeout / connection limit）是被动的。iOS 侧没有直接暴露 supervision timeout 和断开 reason code（Android 有），所以只能靠组合信号推断：有 error 且信号此前 RSSI 骤降 → 大概率超距；设备侧有"关机"notify 特征值 → 用户关机。重连策略分三层：第一层断开后立刻重连一次（超距返回场景恢复最快）；第二层指数退避，比如 1s/2s/4s…封顶 30s，设总预算如 3 分钟；第三层依赖系统——只要在断开状态下保持 `connect(_:options:)` 不 cancel，iOS 会在设备重新进入范围时自动连接，这招在后台尤其关键，因为 App 自己没法在后台持续扫描。配合 `retrievePeripherals(withIdentifiers:)` 用已知 identifier 直连，跳过扫描。

**实战案例**：我们手环断连率高的时候我做了三件事：一是断开原因分类埋点，发现六成是超距短断；二是退避重连 + 保持 connect pending 让系统帮忙；三是重连成功后自动触发增量同步补齐断连期数据。线上断连后 1 分钟内恢复率从约 70% 提到 90%+。<!-- 需替换为真实经历 -->

**边界与权衡**：要注意 `connect` 是"直到成功或取消"语义，一直 pending 会持续功耗，且 iOS 对同时 pending 的连接数有隐性限制；另外频繁断连有时不是 App 的锅，是固件侧连接参数或天线问题，要用 PacketLogger 确认 supervision timeout 是谁踢的，别在 App 层无限重试掩盖固件 bug。

## Q4. iOS 后台 BLE 有哪些限制？App 进后台后如何维持设备通信？

**结论先行**：靠 `bluetooth-central` 后台模式维持已建立连接的通信是可行的，但扫描基本不可用、回调被节流；长期可靠的方案是实现 state preservation & restoration，接受"App 会被杀、靠系统代管连接、重启后恢复"这个模型。

**原理展开**：声明 `UIBackgroundModes: bluetooth-central` 后：已连接设备的 notify/read/write 在后台仍可收发，这正是很多数据同步类产品的工作方式；但 `scanForPeripherals` 在后台被大幅限制——只能扫指定服务 UUID、去重强制开启、回调频率极低，且 App 被挂起后扫描停止。更关键的是 iOS 会代管连接：App 被杀后如果系统仍持有对该设备的 connect 请求，设备事件（如 notify）到达时系统会重新拉起 App 并回调 `centralManager(_:willRestoreState:)`，这里能拿到 restored 的 central、已连接外设和 pending 的扫描服务，我在这个回调里重建内部状态机、重新订阅特征值。初始化 manager 时要传 `CBCentralManagerOptionRestoreIdentifierKey`。后台回调时间片有限，收到数据应尽快处理或落盘，别做重活。

**实战案例**：我们的夜间睡眠监测要求 App 后台整晚接收手环 notify 数据。方案是 bluetooth-central 保活 + restoration，收到 notify 先写入轻量缓冲队列，积累到一定量或前台化时再批量入库。上线初期有零星用户整晚数据缺失，排查发现是系统低电量场景杀掉了 App 且 restoration 恢复后没重新 setNotifyValue——修复恢复流程里"重新订阅"这一步后，整晚数据完整率稳定在 99% 以上。<!-- 需替换为真实经历 -->

**边界与权衡**：要坦白说清边界：bluetooth-central 不保证 App 进程长期存活，它保证的是"连接由系统代管、事件可唤醒"；如果用户手动从多任务划掉 App，系统不会再拉起，这是平台规则绕不过去，产品上要在前台把数据尽量同步完。另外 BGTaskScheduler 不是为 BLE 设计的，别拿它当保活手段。

## Q5. 设计一个固件 OTA 升级方案。

**结论先行**：我会设计成"下载校验 → 自定义 DFU 协议分包传输 → 设备侧 A/B 分区写入 → 校验后原子切换 → 失败自动回滚"的流水线，App 侧的核心职责是可靠传输与断点续传，安全边界（不变砖）必须由固件侧分区方案保证。

**原理展开与方案设计**：
1) **固件包与校验**：固件包带 header（版本号、大小、目标硬件型号、协议版本），整体 SHA-256 做完整性校验，每个分包带序号 + CRC16 做链路层快速校验——哈希保证最终一致，CRC 保证单包快速重传判断，两者不冲突。
2) **分包大小**：理论上限是协商后的 ATT MTU 减 3 字节 ATT header，但实际用设备端可用 buffer 决定，典型做法是 20-244 字节/包。iOS 上用 `maximumWriteValueLength(for:)` 取实际值，写用 `withoutResponse` 拉吞吐、靠设备端流控（写一个 credit 特征值或用 `didWrite` 节流）；配合 Connection Interval 请求到 15ms 左右，1MB 固件实测可在 1-2 分钟传完。
3) **传输协议**：每包带 offset 序号，设备端按序校验，发现丢包/错序时向 App 回传期望 offset，App 从该点重发——这就是断点续传，App 侧持久化当前 offset，App 被杀或断连重连后从设备端查询"已接收进度"续传，而不是从头再来。
4) **防变砖**：设备侧 A/B 双分区（或双 bank），新固件写入 B 区，写完整体哈希校验通过才更新 boot flag 切到 B；启动后自检失败自动回滚 A 区。App 侧只负责"传完 + 确认"，切换决策在固件。
5) **升级流程状态机**：download → verify → connect check（电量 > 30%，连接稳定）→ transfer → device verify → reboot & switch → reconnect & 版本号确认。任何一步失败都有明确回退动作；传输中途断连走断点续传；重启后 App 通过读版本特征值判断升级结果。
6) **灰度与发布**：固件包走服务端配置下发，按设备批次/地区灰度，带紧急回滚开关（把灰度版本下线、推回旧版指引）。
7) **iOS 侧注意点**：OTA 期间 App 尽量前台引导用户保持靠近，后台可做但要有进度恢复；避免与数据同步抢带宽，升级期间暂停常规同步。

**实战案例**：我主导过一次量产手环的 OTA 通道建设：初版用 128 字节分包 + withoutResponse + 设备端 credit 流控，1.2MB 固件平均 90 秒左右传完；上线后针对"传输中断"做了 offset 续传，升级成功率从约 94% 提升到 99%+，且因为固件侧 A/B 分区兜底，全程零变砖事故。<!-- 需替换为真实经历 -->

**边界与权衡**：OTA 的代价是复杂度和时间：A/B 分区要求 flash 容量翻倍，小容量芯片只能做单区 + bootloader 备份方案，续传粒度也更粗；灰度需要服务端基建，早期团队可以先做"手动触发 + 强制版本下限"。另外 OTA 本身要走加密通道（bonding 或应用层加密），防止固件包被替换。

## Q6. BLE 传输吞吐量受限，大批量数据（如一天的传感器数据）怎么高效同步？

**结论先行**：吞吐优化是"MTU × 包速率"的乘法题：协商大 MTU、用 writeWithoutResponse/notify 提高包速率、设备端做压缩和环形缓冲，App 侧做进度预估，四者一起上才能把"一天的数据"从分钟级压到秒级。

**原理展开**：BLE 吞吐 ≈ 每个 connection event 能发的包数 × 每秒 connection event 数。可操作的点：① MTU 协商——iOS 上 ATT MTU 由系统自动协商（iOS 一般可到 185+），App 用 `maximumWriteValueLength(for:)` 拿实际可写长度，别写死 20 字节；② 传输模式选 notify（设备推、无应用层 ACK）或 writeWithoutResponse，比 writeWithResponse 快不少，可靠性靠 L2CAP 层和自定义序号补齐；③ Connection Interval：同步期间请求短 interval（如 15-30ms），同步完恢复长 interval 省电，iOS 侧 App 无法直接改参数，靠固件发起 parameter update request，App 侧能做的是集中传输、缩短高功耗窗口；④ 数据侧：设备端环形缓冲存满前先压缩（传感器数据用 delta encoding + 简单 RLE/LZ4 类压缩常见能到 2-4 倍），按时间戳分块编号传输，App 增量合并。

**实战案例**：我们手环一天约 5-8MB 原始传感器数据，最初全量同步要 6 分钟以上。优化路径：设备端做差分压缩压到 1/3；MTU 按实际 182 字节写满；notify 推送 + 滑动窗口序号确认补传；同步期间固件请求 15ms interval。最终压到 90 秒内，同时 UI 上按"剩余字节 / 当前速率"展示预计时间和百分比，用户中途退出的比例明显下降。<!-- 需替换为真实经历 -->

**边界与权衡**：吞吐和功耗是跷跷板，短 interval 全速传 90 秒可以接受，但不该常态化；另外 iOS 的实际吞吐受射频环境和系统调度影响，同一套参数不同用户能差一倍，所以进度预估要用实时速率而不是理论值，并且永远要做"同步中断可续传"的设计。

## Q7. 设备配对（pairing/bonding）与连接（connection）有什么区别？iOS 上怎么处理？

**结论先行**：连接是建立 ACL 链路进行数据收发，配对是协商加密密钥并可选地 bonding（长期保存密钥），两者独立：可以连接不配对，也可以删除 bonding 后重连触发重新配对。iOS 把配对完全托管给系统，App 没有显式 pairing API。

**原理展开**：配对流程（SMP 层）：feature exchange → 密钥协商（LE Secure Connections 用 ECDH P-256）→ 生成 STK/LTK → bonding 时双方把密钥持久化。触发时机由 GATT 访问驱动：当 App 读写一个要求加密/认证的特征值（固件在 GATT 里设了 encryption/authentication 权限）时，系统自动弹配对框。iOS 侧的表现：配对信息存在系统层（跨 App 共享），App 拿不到密钥；用户在 设置 > 蓝牙 里"忽略此设备"会清除 bonding，下次访问加密特征值时系统会重新弹配对；App 侧能做的感知手段是：读写返回 `CBErrorPeripheralDisconnected` 或加密相关 error 时提示用户重新配对。防 MITM 用 numeric comparison / passkey（LE Secure Connections 下默认有 MITM 防护），Just Works 没有 MITM 防护，只防被动窃听，敏感数据传输要确保固件侧用带认证的配对方式。

**实战案例**：我们产品第一次绑定流程就是靠"访问加密特征值触发系统配对弹窗"实现的，引导文案教用户在弹窗出现时确认；遇到的坑是用户在系统设置里忽略设备后 App 无感知、一直连接失败，后来加了错误分类：识别到配对类失败就引导用户去设置里忽略干净再走重新绑定流程，绑定成功率相关问题客诉降了一半以上。<!-- 需替换为真实经历 -->

**边界与权衡**：iOS 的托管模式省心但失控——App 无法主动发起配对、无法查询 bonding 状态、无法静默解绑，产品上"解绑"只能是 App 层逻辑 + 引导用户去系统设置。相比之下 Android 有 `createBond`/`removeBond`，跨平台协议设计时要把这个差异考虑进去。

## Q8. App 和设备需要保持状态同步（电量、模式、固件状态），你的方案是什么？

**结论先行**：我的模型是"设备是唯一事实源（single source of truth），App 是缓存 + 展示层"：实时变化靠 notify/indicate 推，连接建立时全量拉一遍做对齐，写入用带确认的协议保证最终一致。

**原理展开**：三个问题分开答。以谁为准：设备状态（电量、模式）永远设备说了算，App 本地值只是缓存，带"最后更新时间"，过期就降级显示。推拉结合：连接建立后 App 主动读一遍所有状态特征值（全量对齐）；运行期设备通过 notify 推送变化——notify 和 indicate 的选择：indicate 带应用层 ACK 更可靠但要等确认、延迟高，电量这类高频非关键状态用 notify，固件状态切换这类必须送达的用 indicate 或应用层确认。写冲突：App 写"切换模式"用 writeWithResponse + 设备回执 notify 新状态为准，而不是 App 本地乐观更新；如果两端同时写（很少见，比如物理按键 + App 同时操作），以设备端最后状态为准，App 被 notify 纠正。重连策略：断连时间不可信，重连后一律全量拉一次状态，增量同步只用于数据块而非状态。版本号方案：设备维护一个状态版本号/计数器，App 可先读版本号判断是否需要全量刷新，省一次全读。

**实战案例**：我们手环的状态层就是这么分层的：一个 StateSync 模块统一管理"读对齐 + notify 订阅 + 写确认"，UI 只订阅状态仓库。上线初期出过"App 显示模式和设备实际不符"的 bug，原因是写入后只做了本地乐观更新没等设备确认 notify，改成"写 + 等 confirm notify + 超时回滚"后再没复现。<!-- 需替换为真实经历 -->

**边界与权衡**：这套方案的前提是设备端状态机设计合理、notify 不丢关键事件——如果固件侧事件可能丢（比如 notify 拥塞），关键状态就要定期轮询兜底。另外全量对齐要控制特征值数量和读并发，别一次几十个 read 把链路打满。

## Q9. 蓝牙协议栈大致分几层？GATT、ATT、L2CAP 各是干什么的？

**结论先行**：BLE 协议栈分 Controller（物理层 PHY + 链路层 LL）和 Host（L2CAP、SMP、ATT、GATT、GAP），iOS 开发者日常接触的最底层是 L2CAP，往上 ATT 是传输单元、GATT 是数据组织模型、GAP 管角色与广播。

**原理展开**：自底向上：PHY 管射频调制（BLE 4.x 起 1M/2M/Coded PHY）；Link Layer 管广播、扫描、连接状态机、信道跳频、加密触发；L2CAP 做协议复用和分片重组（把上层大包拆成 LL 能发的分片），还支持 Connection-Oriented Channels（CoC），即 ATT 之外的点对点大数据信道；SMP 管配对和密钥；ATT（Attribute Protocol）定义 client/server 的属性读写模型，handle + UUID + value，是"操作"层；GATT 在 ATT 之上定义 service → characteristic → descriptor 的层级组织模型，是"数据语义"层；GAP 定义角色（central/peripheral/broadcaster/observer）和广播/发现流程。indicate vs notify 都在 GATT 层，靠 characteristic 的 CCC descriptor（0x2902）订阅：notify 无确认、indicate 要 Handle Value Confirmation。和嵌入式团队沟通时这套词汇很关键，比如"丢包"要分清是 LL 层重传失败还是 ATT 层超时。

**实战案例**：有次同步偶发丢数据，App 层日志显示某个 notify 序号断了，我们和固件各持一词；后来用 nRF Sniffer 抓空口包，发现该 connection event 里 LL 层包确实丢了且没重传，是固件侧 RF 参数配置问题——这次之后我们团队约定"先抓包再讨论"，定位效率提升很多。<!-- 需替换为真实经历 -->

**边界与权衡**：iOS 上 CoC L2CAP 信道（`openL2CAPChannel`）可用于大吞吐场景，比 ATT 更省开销，但实际产品中我仍优先 ATT + notify，因为 CoC 在后台支持、系统兼容性和调试工具链上都不如 GATT 成熟，只有确定吞吐瓶颈时才值得切。

## Q10. 如何保证 BLE 通信协议的前后兼容（App 和固件版本不一致时）？

**结论先行**：协议设计默认"版本永远不一致"：显式版本号 + 能力协商 + 严格的新增字段容忍规则 + 双端版本矩阵策略，四件套缺一不可。

**原理展开**：具体做法：① 版本号位置：固件版本放在 GAP 的 Device Information Service（0x180A）里，协议版本单独放一个只读特征值或握手包首字段——硬件版本和协议版本要分开，同一硬件可能跑不同协议。② 能力协商：连接建立后第一步交换 capability（双方协议版本 + 支持的特性位图），后续交互只使用交集能力；App 端维护"固件版本 → 可用功能"的映射表，可服务端下发。③ 报文兼容规则：所有协议带 length 字段；解析按 TLV 或明确 length，未知命令/字段忽略而不是报错；枚举值预留 unknown 分支；禁止复用已定义字段含义，新功能一律新增命令 ID。④ 四种组合：新 App + 旧固件 → 功能降级可用；旧 App + 新固件 → 固件必须兼容旧协议（固件无法强更，这是铁律）；双向都要测。⑤ 运营手段：App 内提示固件过旧引导 OTA；对严重不兼容组合设硬下限（旧 App 连新固件时提示升级 App）。

**实战案例**：我们 v2 固件新增了一组传感器命令，v1 固件还在大量用户手上。做法是握手包里带 protocol version，App 按版本决定下发哪套命令集；报文解析器严格按 length 跳过未知字段。上线期间靠这套规则做到双版本零崩溃、零通信失败投诉，后续协议演进也沿用同一套兼容性守则。<!-- 需替换为真实经历 -->

**边界与权衡**：兼容性的代价是协议臃肿和测试矩阵膨胀——版本组合随时间指数增长，需要自动化回归（协议层的 App/固件双向自动化测试）兜底。我的原则是：兼容规则写进协议文档作为宪法，宁可加新命令也不改旧语义，改旧语义的收益几乎永远抵不上回归成本。

## Q11. 你在 BLE 开发中遇到过的最难的 bug 是什么？怎么定位的？

**结论先行**：最难的是一个"iOS 16 某版本上连接后偶发服务发现卡死、且不回调任何失败"的问题，纯 App 日志无法定位，最后靠 PacketLogger 空口抓包 + 和固件分工排查，定位到是固件对 Service Changed 处理的时序 bug。

**实战案例（STAR）**：
- **Situation**：线上监控发现约 0.3% 的用户连接后拿不到数据，日志停在 `discoverServices` 调用之后、无任何成功或失败回调，且集中在 iOS 16.1-16.2，重装 App 无效。
- **Task**：复现并定位——难点是低概率、跨系统版本、跨端（App / iOS 协议栈 / 固件）。
- **Action**：① 先缩小范围：加了全链路状态埋点后确认卡在服务发现阶段；用 `retrieveConnectedPeripherals` 确认连接其实建立了。② 工具链：Mac 上 PacketLogger 抓 HCI 日志对比正常/异常 case，发现异常 case 里 iOS 发了 ATT Read By Group Type Request 后固件迟迟不回 response，最终 supervision 层超时；用 nRF Sniffer 交叉验证空口行为。③ 和固件分工：我提供抓包时间线，固件侧开日志发现是 GATT 缓存的 Service Changed indication 和新连接的 discover 请求抢同一个发送队列，在特定顺序下死锁。④ 修复：固件调整 indication 时序 + App 侧给服务发现加 10s 超时兜底，超时则断开重连一次。
- **Result**：修复后该错误率归零；团队沉淀了"BLE 疑难问题标准排查流程"（日志 → 状态埋点 → PacketLogger → 空口抓包 → 双端会审），后续类似问题定位时间明显缩短。<!-- 需替换为真实经历 -->

**边界与权衡**：这类跨层 bug 的经验是：不要相信任何一端的"我没问题"，空口包是唯一中立证据；但抓包工具也有盲区（iOS 内部协议栈行为不可见），所以 App 侧的超时兜底和自愈设计永远是第一道防线——定位 bug 的同时要先上线止血方案。

**英文摘要**：The hardest bug was a rare service-discovery deadlock on iOS 16 caused by a firmware timing issue; I pinpointed it with PacketLogger and an air sniffer, then fixed both sides.

## Q12. 如果设备同时被多个 App/系统组件抢占连接，你怎么处理？

**结论先行**：先分清"抢占者"是谁：iOS 上同一 BLE 外设同一时刻只能被一个 central 持有 ACL 连接，其他 App 连不上；但系统组件（如耳机类的系统音频接管）走的是经典蓝牙/系统级通道，规则不同。应对核心是"连接归属检测 + 优雅降级 + 用户引导"。

**原理展开**：iOS 的规则：一个 BLE peripheral 只能被一个 central 连接，第二个 App 调 connect 会失败或一直 pending（`didFailToConnect` 的 error 可能提示 connection limit）。同一厂商的多个 App 之间可通过 App Group 或厂商约定协调，但没有系统级仲裁。对耳机类产品（AirPods 类），系统走经典蓝牙 HFP/A2DP 且有系统级自动切换，App 基本无法干预也不该干预。App 能做的检测手段：`didFailToConnect` 的 error、连接后立刻被踢（`didDisconnectPeripheral` 带特定 error）、`retrieveConnectedPeripherals(withServices:)` 判断设备当前是否已被系统连上（只能查到"被系统/其他持有"这一事实，查不到是谁）。BLE 5.1+ 的 Audio 走的是 LE Audio 另一套体系，和 GATT 连接互不冲突，可以共存。

**实战案例**：我们的设备曾被用户手机上的第三方通用 BLE 调试 App（如 nRF Connect）抢先连住，导致我们的 App 一直连接失败。处理方案：connect 失败或 10 秒未连上时，提示"设备可能被其他应用占用，请关闭蓝牙调试类 App 或重启蓝牙"，并提供重试；同时在文档和客服话术里覆盖了这一场景，这类工单从"疑难杂症"变成了一条标准自助指引。<!-- 需替换为真实经历 -->

**边界与权衡**：要坦率承认 App 层能做的有限——iOS 不提供"强制抢占连接"的 API，也不告知占用者身份，我们能做的上限就是检测 + 引导 + 自愈重试。产品设计上更根本的解法是让设备固件侧实现"白名单/最后绑定设备优先"策略，拒绝陌生 central 的连接请求，这需要和固件团队在协议层约定。
