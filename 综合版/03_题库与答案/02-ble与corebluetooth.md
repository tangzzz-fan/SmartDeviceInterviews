# 题库与答案 · BLE 与 Core Bluetooth（P0，权重最高）

> 用法：本模块是 JD 权重最高的部分（约 25%），每题都要能脱稿讲并现场画图。
> 白板 1（连接/恢复状态机）必须不看稿画出来，详见 [../05_白板图解.md](../05_白板图解.md)。
> 案例中的数字为示范值，必须替换为自己的真实数据。

## B1. 介绍 Core Bluetooth 架构与完整链路。

**答案**：

App 通常扮演 Central（CBCentralManager），设备扮演 Peripheral。GATT 模型上，Peripheral 暴露 Service，Service 里是 Characteristic（可读/可写/notify），Descriptor 描述特征（CCCD 控制 notify 开关）。

CBCentralManager 六态：unknown / resetting / unsupported / unauthorized / poweredOff / poweredOn，只有 poweredOn 可用。`resetting` 表示系统蓝牙子系统重置，所有连接和 pending 操作作废，要清空内部状态等重建；`unauthorized` 引导去系统设置。初始化时序注意：`didUpdateState` 是异步的，poweredOn 之前的 API 调用要排队挂起，不要让调用方各自处理「还没就绪」。

链路是状态机，不是一串 callback：scan（带 service UUID 过滤）→ didDiscover → connect → didConnect → discoverServices → discoverCharacteristics → 订阅与握手 → Ready → 收发 → 断连。每个状态迁移打点上报，每个环节有超时兜底和可取消设计。BLE 回调放在专用串行队列，不用主队列解析数据。

**追问应对**：
- notify 靠 CCCD 启用，App 订阅后外设才推送；iOS 不会自动重连所有外设，得自己实现恢复策略。
- 按需发现服务，别全量 discover：慢，且部分芯片有兼容问题。
- iOS 13+ 需要 NSBluetoothAlwaysUsageDescription。

## B2. Ready 的定义是什么？为什么不在 didConnect 就允许发命令？

**答案**：

`didConnect` 只代表链路建立，此时服务未发现、MTU 未交换、设备可能还在初始化，这时发命令是随机故障的来源。Ready 的定义是三个条件同时满足：**关键 characteristic 可写、notify 已订阅、握手（版本/能力交换）通过**。之后才允许业务命令进入队列。

案例：曾把「已连接」当「可用」，用户点按钮偶发无响应，根因是命令在服务发现完成前就发出。改成状态机控制命令入队时机后，此类客诉清零。

**取舍**：发现全部服务更稳但慢；生产上只发现需要的服务，超时则失败并重试，而不是挂起。

## B3. 扫描与连接的最佳实践？扫描不到设备怎么排查？

**答案**：

扫描按 service UUID 过滤——后台扫描的硬性要求，也省电；前台可开 allowDuplicates 做 RSSI 过滤。维护扫描定时器（如 10 秒）避免无限扫描，扫到目标 stopScan 再 connect。设备匹配不能只看名字：manufacturer data 带协议号和序列号区分同型号多台设备，RSSI 阈值（如 -70dBm）防连到远处设备。连接成功保存 peripheral.identifier，下次直连不重扫。

扫描不到的分层排查：
1. 系统层：`CBManager.state`、Info.plist、蓝牙权限、精确位置（若需要）；
2. 广播层：用 nRF Connect 等第三方工具确认广播在不在；
3. 过滤层：App 过滤条件是否过严——名字、UUID、manufacturer data 版本变更是高频坑；
4. 固件层：是否已连接后停广播、低功耗下是否拉长了广播 interval。

**追问应对**：已绑定设备优先 `retrievePeripherals` / `retrieveConnectedPeripherals` 直连，扫描当补充。

**取舍**：放宽过滤能提高发现率，误连风险上升。已绑定走 identifier，未绑定才用可解释的广播字段。

## B4. 连接参数怎么调优？

**答案**：

三参数：connection interval（7.5ms–4s）、slave latency（外设可跳过的事件数）、supervision timeout（超过即判定断连，须大于 interval 的合理倍数）。直接 tradeoff 吞吐、时延、功耗。

按场景动态调参：实时指令要低时延，interval 拉小；批量同步短暂收紧 interval 冲吞吐；空闲期调大 interval + 提高 latency 省电。iOS 上参数更新请求由外设发起，central 有裁决权，iOS 对参数有上限限制，要留余量。supervision timeout 留大一点，避免弱信号误判断连。

**追问应对**：iOS 实际吞吐受连接事件频率、ATT MTU、PHY（1M/2M/CODED）共同限制，调参只解决一部分。

## B5. MTU 与吞吐怎么优化？大批量传感器数据怎么同步？

**答案**：

ATT MTU 默认 23 字节，有效载荷 20（减 3 字节 ATT 头），协商后 iOS 可到 185+（上限 517）。iOS 由系统自动协商，App 用 `maximumWriteValueLength(for:)` 拿实际可写长度，别写死 20 字节。

吞吐是「MTU × 包速率」的乘法题：吞吐 ≈ 每 connection event 发包数 × 每秒 connection event 数。四个抓手：
1. **MTU**：按实际协商值写满；
2. **传输模式**：notify（设备推、无应用层 ACK）或 writeWithoutResponse 比 writeWithResponse 快；withoutResponse 要配合 `canSendWriteWithoutResponse` 与 `peripheralIsReady(toSendWriteWithoutResponse:)` 做流控，可靠性靠序号补齐；
3. **Interval**：同步期固件请求短 interval（15–30ms），传完恢复长 interval 省电；
4. **数据侧**：设备端环形缓冲 + 压缩（delta encoding + RLE/LZ4 常见 2–4 倍），按时间戳分块编号传输，App 增量合并。

大文件传输：分块 + 序号 + CRC，断点续传（记录 offset），窗口批量确认。实测量级：2M PHY + 大 MTU 下 notify 数百 KB/s；一天 5–8MB 传感器数据可从 6 分钟压到 90 秒内。进度预估用实时速率不用理论值——同一套参数不同用户能差一倍。

**取舍**：吞吐和功耗是跷跷板，短 interval 全速传 90 秒可接受，不能常态化。

## B6. 设备与 App 状态同步怎么保证一致？（电量/模式/固件状态）

**答案**：

模型：**设备是唯一事实源，App 是缓存 + 展示层**。三个问题分开：

1. **以谁为准**：设备状态永远设备说了算，App 本地值只是带「最后更新时间」的缓存，过期降级显示 stale。
2. **推拉结合**：连接建立后 App 主动读一遍状态特征值做全量对齐；运行期设备 notify 推送变化。notify vs indicate：电量这类高频非关键状态用 notify，固件状态切换这类必须送达的用 indicate 或应用层确认。
3. **写冲突**：写「切换模式」用 writeWithResponse + 等设备回执 notify 新状态为准，不做本地乐观更新；两端同时写（物理按键 + App）以设备端最后状态为准，App 被 notify 纠正。

数据帧不丢不重：序列号 + 时间戳 + CRC；写路径有确认；定期对账——设备返回最新 seq，App 从断点补拉。离线场景设备侧持久化未同步数据（环形缓冲/Flash），App 侧把「已确认到哪」也持久化，重启也能续传。冲突规则提前定：版本号、last-write-wins 或服务器裁决；健康数据以设备端记录为准。

**追问应对**：
- 状态版本号/计数器让 App 先判断是否需要全量刷新，省一次全读。
- 时钟不同步用设备单调计数 + App 对时，不做跨设备绝对时间比较。
- 若固件侧 notify 可能丢（拥塞），关键状态定期轮询兜底。

**案例**：UI 显示模式与设备不符的 bug，根因是写入后只做本地乐观更新没等设备确认；改成「写 + 等 confirm notify + 超时回滚」后未复现。

## B7. 断连与异常恢复策略？

**答案**：

核心：**先分类断连，再受控重连。目标不是「重新连上」，而是「重新回到可信状态」。**

断连三分类：
- 用户主动断开 → Idle，不自动重连；
- 蓝牙关闭/权限问题 → WaitSystem，提示用户；
- 链路异常 → Reconnecting，有限次数 + 指数退避。

`didDisconnectPeripheral` 带 error：nil 通常本端主动断，非 nil 是被动的。iOS 不暴露断开 reason code，靠组合信号推断：RSSI 骤降 → 大概率超距；设备有「关机」notify → 用户关机。

重连三层：① 断开后立刻重连一次（超距返回恢复最快）；② 指数退避 + 抖动（1s/2s/4s/8s 封顶），设总预算（如 3 分钟），前台间隔短、后台/低电量拉长或暂停；③ 依赖系统——断开后保持 `connect` 不 cancel，设备重新进范围时 iOS 自动连接，后台尤其关键（App 没法后台持续扫描）。

恢复后走现场重建：重新发现/确认订阅、snapshot 拉关键状态、reconcile 本地预期 vs 设备实际、续传未完成任务（OTA/上传队列）；若系统清了绑定，走重新 bonding。命令带 seq/requestId 保证幂等，ack 未到不当成功。

量化指标：重连成功率、断连后 1 分钟恢复率（示范：70% → 90%+）、平均恢复时长。

**追问应对**：
- 无限重连为什么不行？耗电、打满日志、和固件侧连接资源打架，还把真正的硬件故障掩盖成「一直在重试」。
- 频繁断连有时是固件连接参数或天线问题，用 PacketLogger 确认 supervision timeout 是谁踢的，别在 App 层无限重试掩盖固件 bug。

**取舍**：激进重连体验上「比较连得上」，功耗和稳定性更差。给重试预算和用户可见状态。

## B8. iOS 后台 BLE 有哪些限制？如何维持设备通信？

**答案**：

声明 `UIBackgroundModes: bluetooth-central` 后：已连接设备的 notify/read/write 后台仍可收发；但扫描被大幅限制——只能扫指定 UUID、强制去重、回调频率极低，挂起后扫描停止。

长期可靠方案是 **State Restoration**：初始化 manager 传 `CBCentralManagerOptionRestoreIdentifierKey`；App 被杀后若系统仍持有 connect 请求，设备事件到达时系统拉起 App 并回调 `willRestoreState`，在这里重建状态机、**重新 setNotifyValue 订阅**、业务握手要自己重做——restoration 通常只恢复 manager 和外设对象，恢复不到 Ready。

后台回调时间片有限，收到数据尽快处理或落盘（先写轻量缓冲队列，前台化再批量入库），别做重活。

**边界必须坦白**：bluetooth-central 保证的是「连接由系统代管、事件可唤醒」，不是进程长期存活；用户从多任务划掉 App 后系统不会拉起，产品上要在前台把数据尽量同步完。BGTaskScheduler 不是为 BLE 设计的，别拿它当保活手段。

**案例**：夜间睡眠监测整晚后台收 notify。上线初期低电量场景系统杀 App，restoration 恢复后漏了重新订阅导致整晚数据缺失；补上「重新订阅」步骤后数据完整率稳定 99%+。

## B9. OTA 怎么设计？

**答案**：

完整链路（对应白板 2）：条件检查（型号/电量/版本/是否充电）→ 下载固件 + 整体校验（SHA-256/签名）→ 进入 OTA 模式 → 分片传输（每包 offset + CRC16，credit/ack 窗口流控）→ 设备侧整体校验 → 重启切换 → 重连 + 版本号确认 + smoke 验证。

可靠性设计：
- **断点续传**：App 持久化 offset；断连重连后向设备查询「已接收进度」续传，而不是从头再来。
- **防变砖**：设备侧 A/B 双分区，新固件写 B 区，校验通过才更新 boot flag；启动自检失败自动回滚。切换决策在固件，App 只负责「传完 + 确认」。
- **commit 点**：未提交新镜像前保持旧镜像可启动；传输中断设备保持可连；超时退出 OTA 模式重新广播。
- **电量约束**：低于阈值（如 30%）拒绝升级；传输期间防关机。
- **防降级/刷错型号**：包里带 hardware revision 和最小版本，签名失败直接拒绝。
- 传输走加密通道（bonding 或应用层加密），防固件包被替换。

分包大小用 `maximumWriteValueLength(for:)` 实测，writeWithoutResponse 拉吞吐 + 设备端流控；同步期间请求短 interval，1MB 固件实测 1–2 分钟。OTA 期间暂停常规数据同步，避免抢带宽。

失败路径必须设计：下载失败不进升级模式；校验失败丢包保旧固件；重启后连不上走超时窗口 + 恢复模式（与固件约定）；版本不匹配拒绝启动新功能并上报。灰度按设备批次/地区下发，带回滚开关。

**案例**：试产时升级到 80% 掉电，和固件约定「未提交前旧镜像可启动 + 断点续传 + 超时退出 OTA」，App 每阶段打点，OTA 成功率 92% → 99%+，零变砖。

**取舍**：A/B 分区最安全但 flash 成本翻倍；小容量芯片只能单区 + bootloader 备份，续传粒度更粗。没做过完整量产 OTA 时用 [02_差距地图](../02_差距地图与补强策略.md) 缺口话术 1。

## B10. 配对、绑定与安全怎么处理？

**答案**：

先分清概念：**连接**是建立 ACL 链路收发数据；**配对**是协商加密密钥，可选 bonding（长期保存密钥）。两者独立：可连接不配对，也可删 bonding 后重连触发重新配对。

iOS 把配对完全托管给系统，App 没有显式 pairing API：当读写要求加密/认证的特征值时，系统自动弹配对框；密钥存在系统层跨 App 共享，App 拿不到。用户在设置里「忽略此设备」会清 bonding，下次访问加密特征值重新弹窗。

安全等级：legacy 配对 MITM 风险高；LE Secure Connections 用 ECDH P-256，numeric comparison / passkey 有 MITM 防护；Just Works 只防被动窃听——敏感数据要确保固件侧用带认证的配对方式。健康数据在 characteristic 加密之上，应用层再加密一层，云端走 TLS。

要处理的场景：rebond（重绑清旧密钥）、「设备已被另一台手机绑定」的提示与解绑引导、用户在系统设置忽略设备后 App 无感知一直连接失败——做错误分类，识别配对类失败就引导用户忽略干净再走重新绑定流程。

**取舍**：iOS 托管模式省心但失控——无法主动发起配对、无法查询 bonding 状态、无法静默解绑；「解绑」只能是 App 层逻辑 + 引导。跨平台协议设计要把和 Android（createBond/removeBond）的差异考虑进去。

## B11. BLE 协议栈大致分几层？

**答案**：

Controller（PHY + Link Layer）+ Host（L2CAP、SMP、ATT、GATT、GAP）。iOS 开发者日常接触最底层是 L2CAP。

- **PHY**：射频调制，1M/2M/Coded PHY；
- **Link Layer**：广播、扫描、连接状态机、跳频、加密触发；
- **L2CAP**：协议复用与分片重组，另有 CoC 点对点大数据信道；
- **SMP**：配对与密钥；
- **ATT**：属性读写模型（handle + UUID + value），「操作」层；
- **GATT**：service → characteristic → descriptor 组织模型，「数据语义」层；
- **GAP**：角色与广播/发现流程。

和嵌入式团队沟通这套词汇很关键：「丢包」要分清是 LL 层重传失败还是 ATT 层超时。

**追问应对**：iOS 的 L2CAP CoC（`openL2CAPChannel`）大吞吐更省开销，但后台支持、兼容性、工具链都不如 GATT 成熟，只有确定吞吐瓶颈才切换。

## B12. 如何保证协议前后兼容（App 和固件版本不一致）？

**答案**：

默认「版本永远不一致」，四件套缺一不可：

1. **版本号位置**：固件版本放 Device Information Service（0x180A），协议版本单独放只读特征值或握手包首字段——硬件版本和协议版本分开；
2. **能力协商**：连接后第一步交换 capability（协议版本 + 特性位图），只用交集能力；App 维护「固件版本 → 可用功能」映射表，可服务端下发；
3. **报文兼容规则**：所有协议带 length 字段，按 TLV 或明确 length 解析；未知命令/字段忽略而不是报错；枚举预留 unknown 分支；禁止复用已定义字段含义，新功能一律新增命令 ID；
4. **四种组合测试**：新 App + 旧固件 → 功能降级可用；旧 App + 新固件 → 固件必须兼容旧协议（固件无法强更，铁律）；双向都测。

运营手段：App 内提示固件过旧引导 OTA；严重不兼容组合设硬下限。

**取舍**：兼容性代价是协议臃肿和测试矩阵指数增长，需协议层双向自动化回归兜底。原则：兼容规则写进协议文档当宪法，宁可加新命令也不改旧语义。

## B13. BLE 功耗怎么优化？

**答案**：

四层：
- **连接层**：空闲期调大 interval + slave latency，同步期短暂收紧；
- **扫描层**：缩短扫描窗口、service 过滤、避免高频扫描，后台绝不空扫描；
- **数据层**：外设聚合数据批量 notify，避免逐条推送——同样的数据量少唤醒几次；
- **App 层**：减少后台唤醒、合并 BGTask、不常开定位和网络。

测量闭环：Xcode Energy Log / Instruments Energy 看趋势，真机电流计测绝对功耗，优化前后出数字（示范：空闲连接电流靠 interval 30ms → 300ms + latency 2 明显下降），不然都是拍脑袋。先和产品定功耗 SLA（「实时」和电池寿命直接冲突），再选旋钮。

分工：连接参数和推送策略必须 App 与固件一起定，App 侧能做的只是不添乱。详见 [04_加分项_硬件专题.md](../04_加分项_硬件专题.md)。

## B14. 讲一个 BLE 最难的 bug。连接被其他 App 抢占怎么处理？

**答案（疑难 bug 模板）**：

示范故事（必须替换为真实经历）：iOS 某版本连接后偶发服务发现卡死、不回调任何失败，约 0.3% 用户受影响，重装无效。定位路径：
1. 全链路状态埋点缩小范围，确认卡在服务发现阶段；用 `retrieveConnectedPeripherals` 确认连接其实建立了；
2. PacketLogger 抓 HCI 日志对比正常/异常 case，发现 ATT Read By Group Type Request 后固件迟迟不回 response，最终 supervision 超时；nRF Sniffer 交叉验证空口；
3. 与固件分工：固件日志发现 Service Changed indication 和新连接 discover 抢同一发送队列，特定顺序死锁；
4. 修复：固件调 indication 时序 + App 给服务发现加 10s 超时兜底，超时断开重连一次。

结果：错误率归零，沉淀「BLE 疑难问题标准排查流程」（日志 → 状态埋点 → PacketLogger → 空口抓包 → 双端会审）。

**边界**：不要相信任何一端的「我没问题」，空口包是唯一中立证据；但抓包也有盲区，App 侧超时兜底和自愈设计永远是第一道防线——定位的同时先上线止血方案。

**答案（连接抢占）**：

iOS 规则：一个 BLE peripheral 同一时刻只能被一个 central 持有 ACL 连接，第二个 App connect 会失败或 pending。App 的检测手段：`didFailToConnect` 的 error、连接后立刻被踢、`retrieveConnectedPeripherals(withServices:)` 判断是否被系统/其他持有（查不到是谁）。处理 = 检测 + 引导（提示关闭调试类 App 或重启蓝牙）+ 自愈重试。更根本的解法在固件侧：白名单/最后绑定设备优先，拒绝陌生 central，需要协议层约定。iOS 不提供强制抢占 API，这个边界要坦率承认。
